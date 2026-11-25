"""SAFEIER / QZLGD heated socks battery monitor."""

from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .protocol import SockStatus, async_read_status

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

type SafeierConfigEntry = ConfigEntry[SafeierCoordinator]


class SafeierCoordinator(DataUpdateCoordinator[SockStatus]):
    """Polls one sock battery."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.data[CONF_ADDRESS]}",
            update_interval=SCAN_INTERVAL,
        )
        self.address: str = entry.data[CONF_ADDRESS]

    async def _async_update_data(self) -> SockStatus:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            # Battery only advertises while a sock is plugged in.
            raise UpdateFailed("Akku nicht in Reichweite oder keine Socke eingesteckt")
        try:
            return await async_read_status(ble_device)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Abfrage fehlgeschlagen: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: SafeierConfigEntry) -> bool:
    coordinator = SafeierCoordinator(hass, entry)
    # Don't block setup if the battery is currently off.
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SafeierConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
