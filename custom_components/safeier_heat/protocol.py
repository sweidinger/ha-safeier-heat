"""BLE protocol of the Pinguan PG-xxxxA 'vm' heated sock battery (SAFEIER app)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import NOTIFY_CHAR, RESPONSE_TIMEOUT, STATUS_QUERY, VOLTAGE_CURVE_MV, WRITE_CHAR


@dataclass
class SockStatus:
    """Decoded status frame."""

    device_type: int
    heating: bool
    setpoint: int  # °C
    voltage_mv: int
    timer_min: int
    flash_heating: bool
    raw: str

    @property
    def battery_percent(self) -> float:
        return voltage_to_percent(self.voltage_mv)


def voltage_to_percent(mv: int) -> float:
    """Same curve the vendor app uses."""
    if mv <= VOLTAGE_CURVE_MV[0][0]:
        return 0.0
    if mv >= VOLTAGE_CURVE_MV[-1][0]:
        return 100.0
    for (v0, p0), (v1, p1) in zip(VOLTAGE_CURVE_MV, VOLTAGE_CURVE_MV[1:]):
        if v0 <= mv < v1:
            return round(p0 + (mv - v0) / (v1 - v0) * (p1 - p0), 1)
    return 0.0


def parse_status(data: bytes) -> SockStatus:
    """Parse '55 00 07 TT PP SS VV VV DD FF xx AA'."""
    if len(data) < 11 or data[0] != 0x55:
        raise ValueError(f"unexpected frame {data.hex(' ')}")
    vol = int.from_bytes(data[6:8], "big")
    # App: values 0..4 / 10..40 are coarse bar levels, otherwise voltage in 10 mV.
    voltage_mv = vol * 10 if 250 <= vol <= 500 else vol if 2500 <= vol <= 5000 else 0
    setpoint = data[4] - 5
    if setpoint < 10:
        setpoint = 75
    return SockStatus(
        device_type=data[3],
        heating=data[5] == 0x01,
        setpoint=setpoint,
        voltage_mv=voltage_mv,
        timer_min=data[8],
        flash_heating=data[9] == 0x01,
        raw=data.hex(" "),
    )


async def async_read_status(ble_device: BLEDevice) -> SockStatus:
    """Connect, ask for status once, disconnect (keeps the phone app usable)."""
    loop = asyncio.get_running_loop()
    future: asyncio.Future[bytes] = loop.create_future()

    def _on_notify(_sender, data: bytearray) -> None:
        if not future.done() and len(data) >= 11 and data[0] == 0x55:
            future.set_result(bytes(data))

    client = await establish_connection(
        BleakClientWithServiceCache,
        ble_device,
        ble_device.name or ble_device.address,
        max_attempts=3,
    )
    try:
        await client.start_notify(NOTIFY_CHAR, _on_notify)
        await client.write_gatt_char(WRITE_CHAR, STATUS_QUERY, response=False)
        data = await asyncio.wait_for(future, RESPONSE_TIMEOUT)
    finally:
        await client.disconnect()
    return parse_status(data)
