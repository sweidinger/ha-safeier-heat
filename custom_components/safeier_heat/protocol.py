"""BLE protocol of the Pinguan PG-xxxxA 'vm' heated sock battery (SAFEIER app)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import (
    NOTIFY_CHAR,
    QUERY_REPEATS,
    QUERY_SPACING,
    RESPONSE_TIMEOUT,
    SETPOINT_MAX,
    SETPOINT_MIN,
    STATUS_QUERY,
    VOLTAGE_CURVE_MV,
    WRITE_CHAR,
)


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
    raw_voltage_mv: int = 0

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


def build_command(setpoint: int, heating: bool, timer_min: int, flash: bool) -> bytes:
    """'55 01 05 TT PP SS DD FF 00 AA' – same frame the SAFEIER app sends."""
    setpoint = max(SETPOINT_MIN, min(SETPOINT_MAX, int(setpoint)))
    return bytes(
        [0x55, 0x01, 0x05, 0x00, setpoint + 5, 0x01 if heating else 0x00,
         max(0, min(255, int(timer_min))), 0x01 if flash else 0x00, 0x00, 0xAA]
    )


async def async_read_status(ble_device: BLEDevice, command: bytes | None = None) -> SockStatus:
    """Connect, optionally send a command, read status, disconnect.

    The status is queried a few times and the lowest voltage is kept; the
    newest frame gives on/off and setpoint. Disconnecting after every
    exchange keeps the phone app usable.
    """
    frames: list[bytes] = []
    accept = False

    def _on_notify(_sender, data: bytearray) -> None:
        # Status replies start with 55 00; command acks with 55 01.
        if accept and len(data) >= 11 and data[0] == 0x55 and data[1] == 0x00:
            frames.append(bytes(data))

    client = await establish_connection(
        BleakClientWithServiceCache,
        ble_device,
        ble_device.name or ble_device.address,
        max_attempts=3,
    )
    try:
        await client.start_notify(NOTIFY_CHAR, _on_notify)
        if command is not None:
            await client.write_gatt_char(WRITE_CHAR, command, response=False)
            await asyncio.sleep(0.6)
        accept = True
        for _ in range(QUERY_REPEATS):
            await client.write_gatt_char(WRITE_CHAR, STATUS_QUERY, response=False)
            await asyncio.sleep(QUERY_SPACING)
        if not frames:
            deadline = asyncio.get_running_loop().time() + RESPONSE_TIMEOUT
            while not frames and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.2)
        if not frames:
            raise TimeoutError("keine Antwort vom Akku")
    finally:
        await client.disconnect()

    status = parse_status(frames[-1])
    voltages = [v for v in (parse_status(f).voltage_mv for f in frames) if v]
    if voltages:
        status.voltage_mv = min(voltages)
    status.raw_voltage_mv = status.voltage_mv
    return status
