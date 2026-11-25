"""SAFEIER / QZLGD heated socks battery monitor and control."""

from __future__ import annotations

import asyncio
from collections import deque
import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from homeassistant.util import dt as dt_util

from .const import DOMAIN, SCAN_INTERVAL, VOLTAGE_WINDOW
from .protocol import SockStatus, async_read_status, build_command

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

type SafeierConfigEntry = ConfigEntry[SafeierCoordinator]


class SafeierCoordinator(DataUpdateCoordinator[SockStatus]):
    """Polls and controls one sock battery."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.data[CONF_ADDRESS]}",
            update_interval=SCAN_INTERVAL,
        )
        self.address: str = entry.data[CONF_ADDRESS]
        self._lock = asyncio.Lock()
        self._samples: deque[tuple] = deque()

    def _filter_voltage(self, status: SockStatus) -> SockStatus:
        """Report the lowest reading of the window as cell voltage."""
        now = dt_util.utcnow()
        if self._samples and self._samples[-1][2] != status.heating:
            # Load changed: the cell recovers or sags, start over.
            self._samples.clear()
        if status.raw_voltage_mv:
            self._samples.append((now, status.raw_voltage_mv, status.heating))
        while self._samples and now - self._samples[0][0] > VOLTAGE_WINDOW:
            self._samples.popleft()
        if self._samples:
            status.voltage_mv = min(s[1] for s in self._samples)
        return status

    def _ble_device(self):
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            # Battery only advertises while a sock is plugged in.
            raise UpdateFailed("Akku nicht in Reichweite oder keine Socke eingesteckt")
        return ble_device

    async def _async_update_data(self) -> SockStatus:
        async with self._lock:
            ble_device = self._ble_device()
            try:
                return self._filter_voltage(await async_read_status(ble_device))
            except Exception as err:  # noqa: BLE001
                raise UpdateFailed(f"Abfrage fehlgeschlagen: {err}") from err

    async def async_set(
        self,
        *,
        heating: bool | None = None,
        setpoint: int | None = None,
        timer_min: int | None = None,
        flash: bool | None = None,
    ) -> None:
        """Change one or more settings, keep the others as they are."""
        current = self.data
        if current is None:
            raise HomeAssistantError("Akku nicht erreichbar")
        command = build_command(
            setpoint=current.setpoint if setpoint is None else setpoint,
            heating=current.heating if heating is None else heating,
            timer_min=current.timer_min if timer_min is None else timer_min,
            flash=current.flash_heating if flash is None else flash,
        )
        async with self._lock:
            try:
                ble_device = self._ble_device()
                status = await async_read_status(ble_device, command)
            except Exception as err:  # noqa: BLE001
                raise HomeAssistantError(f"Befehl fehlgeschlagen: {err}") from err
        self.async_set_updated_data(self._filter_voltage(status))


async def async_setup_entry(hass: HomeAssistant, entry: SafeierConfigEntry) -> bool:
    coordinator = SafeierCoordinator(hass, entry)
    # Don't block setup if the battery is currently off.
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SafeierConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
