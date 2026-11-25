# SAFEIER / QZLGD Heated Socks – Home Assistant

Local Bluetooth integration for app-controlled heated sock batteries made by
Dongguan Pinguan Sports Technology (PG-6000A and siblings), sold as QZLGD, VEVOR
and others and controlled by the *SAFEIER* app.

## Entities

| Entity | Description |
|---|---|
| Battery | Charge in %, same voltage curve as the vendor app |
| Cell voltage | Raw cell voltage |
| Setpoint | Selected heating temperature |
| Heating | Heating on/off |
| Raw frame | Diagnostic, disabled by default |

## How it works

The battery only advertises (as `vm-00-…`) while a sock is plugged in. Every 60 s
the integration connects, writes the read-only status query `55 01 00 AA` to
characteristic `7202`, reads the reply from `7201` and disconnects again, so the
phone app can still connect in between.

Reply frame: `55 00 07 TT PP SS VV VV DD FF 00 AA`

* `TT` device type (`00` = socks)
* `PP` setpoint + 5 °C
* `SS` `01` = heating on
* `VV VV` cell voltage in 10 mV (big endian)
* `DD` timer in minutes, `FF` flash heating

Requires a connectable Bluetooth adapter or an ESPHome Bluetooth proxy with
`active: true` in range of the socks.

## Installation

HACS → Custom repositories → add this repo (type *Integration*), install, restart
Home Assistant. Batteries are discovered automatically once a sock is plugged in.
