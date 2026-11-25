"""Constants for the SAFEIER / QZLGD heated socks integration."""

from datetime import timedelta

DOMAIN = "safeier_heat"

NOTIFY_CHAR = "00007201-0000-1000-8000-00805f9b34fb"
WRITE_CHAR = "00007202-0000-1000-8000-00805f9b34fb"

# Read-only status query, the vendor app sends it every 10 s.
STATUS_QUERY = bytes.fromhex("550100aa")

SCAN_INTERVAL = timedelta(seconds=60)
RESPONSE_TIMEOUT = 8.0

# Piecewise-linear voltage -> percent curve, taken from the SAFEIER app.
VOLTAGE_CURVE_MV = [
    (3279, 0.0),
    (3609, 25.0),
    (3795, 50.0),
    (3904, 75.0),
    (4085, 100.0),
]

# Temperature range the app allows for 'vm' batteries.
SETPOINT_MIN = 45
SETPOINT_MAX = 75
TIMER_OPTIONS = [0, 20, 40, 60, 90]  # minutes, 0 = no timer
