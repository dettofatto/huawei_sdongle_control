# Huawei SDongle - Local Power Limit Control for Home Assistant

> **Reverse engineered by a surgeon, not a developer.**  
> Protocol discovered via Android pcap capture (PCAPdroid) and Modbus analysis with AI assistance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.x-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-compatible-41BDF5)

---

## Why this exists — the real problem

In Huawei solar installations with **multiple inverters** (master + one or more slaves), each inverter only knows its own output. If you want to limit the **total power exported to the grid**, you cannot simply tell each inverter "limit to X watts" — the individual inverter registers only accept a per-unit limit, not a combined total. They don't coordinate with each other.

The **SDongle A-05** is the gateway that sits above all inverters and manages the entire installation. This script talks **directly to the SDongle**, which then distributes the curtailment across all connected inverters automatically. This is the only way to correctly limit total grid export in a multi-inverter setup.

### Why grid voltage matters — and why inverters shut down

In many grids (especially in Italy under CEI 0-21 / EN 50549), when solar production is high and local consumption is low, excess energy pushed to the grid causes the **grid voltage to rise**. When voltage exceeds **253V**, inverters are required by law to disconnect and shut down.

This creates a painful cycle: inverter shuts down → restarts → shuts down again — stressing the hardware and losing production.

**The solution:** monitor grid voltage in Home Assistant with any compatible energy meter (Shelly EM, Eastron SDM, etc.) and **proactively reduce the export limit** before the inverter hits 253V. This script enables exactly that workflow.

---

## What it does

Controls the **total export power limit** of a Huawei solar installation locally, without cloud, acting directly on the SDongle A-05 gateway — not on individual inverters.

- ✅ Acts on **combined total output** — SDongle distributes the limit across all inverters automatically
- ✅ Works with **any number of inverters** (master + slaves) on the same SDongle
- ✅ Set power limit from **5000W to 18500W** (adjustable to your installation)
- ✅ Read current status (mode, limit) as **JSON**
- ✅ Works **offline** — no Huawei cloud required
- ✅ Integrates with **Home Assistant** via `shell_command` + `command_line` sensor
- ✅ **30-second polling** for real-time status
- ✅ Pairs with a **grid voltage sensor** to prevent inverter shutdown at 253V

---

## Recommended: voltage-based automation

```yaml
alias: "Sdongle - Riduci potenza se tensione alta"
trigger:
  - platform: numeric_state
    entity_id: sensor.grid_voltage   # <-- your voltage sensor
    above: 252
actions:
  - service: input_number.set_value
    target:
      entity_id: input_number.solar_power_limit
    data:
      value: 10000  # reduce to 10kW

---

alias: "Sdongle - Ripristina potenza se tensione ok"
trigger:
  - platform: numeric_state
    entity_id: sensor.grid_voltage
    below: 249
actions:
  - service: input_number.set_value
    target:
      entity_id: input_number.solar_power_limit
    data:
      value: 18500  # restore maximum
```

---

## Requirements

- Huawei SDongle A-05 (tested on firmware `V200R022C10SPC300`)
- Raspberry Pi (or any Linux box) connected to SDongle WiFi (`SDongleA-HVxxxxxxxxxx`)
- NAT/port-forward from LAN → SDongle:

```bash
# Run once on Raspberry Pi (persists after reboot)
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf && sysctl -p

nft add table ip nat
nft add chain ip nat prerouting { type nat hook prerouting priority dstnat \; }
nft add rule ip nat prerouting iifname eth0 tcp dport { 502, 6606 } dnat to 192.168.200.1
nft add chain ip nat postrouting { type nat hook postrouting priority srcnat \; }
nft add rule ip nat postrouting oifname wlan0 masquerade
```

---

## Installation

1. Copy `set_limit.py` to `/config/scripts/set_limit.py` on your Home Assistant instance
2. Edit the top of the script with your settings:

```python
HOST     = 'ip.sdongle'  # Or Raspberry Pi LAN IP; or box, or another wifi connected directly to sdongle
PORT     = 6606
PASSWORD = 'Changeme'      # SDongle installer password
MIN_W    = 5000
MAX_W    = 18500
```

3. Add to `configuration.yaml`:

```yaml
shell_command:
  set_solar_limit: "python3 /config/scripts/set_limit.py {{ watts | int }}"

command_line:
  - sensor:
      name: "Sdongle Stato"
      command: "python3 /config/scripts/set_limit.py status"
      scan_interval: 30
      value_template: "{{ value_json.power_limit_w }}"
      unit_of_measurement: "W"
      json_attributes:
        - mode_name
        - mode
        - status
        - error

input_number:
  solar_power_limit:
    name: "Limite Potenza Solare"
    min: 5000
    max: 18500
    step: 500
    unit_of_measurement: W
    icon: mdi:solar-power
    mode: slider
```

4. Add the automation (via UI → YAML mode):

```yaml
alias: Sdongle - Imposta limite potenza
description: Invia il limite al dongle quando input_number cambia
triggers:
  - trigger: state
    entity_id: input_number.solar_power_limit
conditions: []
actions:
  - action: shell_command.set_solar_limit
    data:
      watts: "{{ states('input_number.solar_power_limit') | int }}"
mode: single
max_exceeded: silent
```

5. Restart Home Assistant

---

## Usage

### From command line:
```bash
# Set limit to 15kW
python3 set_limit.py 15000

# Read current status
python3 set_limit.py status
```

### JSON output examples:

**Status:**
```json
{"status": "ok", "power_limit_w": 18000, "mode": 6, "mode_name": "Active Scheduling"}
```

**Set limit:**
```json
{"status": "ok", "power_limit_w": 15000, "power_limit_previous_w": 18000, "mode": 6, "mode_name": "Active Scheduling"}
```

**Error:**
```json
{"status": "error", "error": "Login failed"}
```

---

## Control Modes

| Value | Name | Description |
|-------|------|-------------|
| `0` | Unlimited | No export limit |
| `1` | Fixed | Fixed per-inverter static limit — does **not** work for combined total |
| `6` | Active Scheduling | Dynamic total limit via SDongle — used by this script |

> **Note:** Mode `6` (Active Scheduling) is the only mode that allows controlling the **combined total** export. Mode `1` (Fixed) applies independently to each inverter and cannot accept a combined total value. This script writes `0xB937 = 6` as an unlock step before writing the limit to `0xB938`.

---

## Protocol Notes

The SDongle communicates on TCP port 6606 using a proprietary Modbus-based protocol.

| Detail | Value |
|--------|-------|
| Port | TCP 6606 |
| Unit ID (dongle) | `0x64` (100) |
| Auth | HMAC-SHA256(SHA256(password), 16-byte challenge) |
| Register mode | `0xB937` — control mode |
| Register limit | `0xB938` — power limit (uint32 BE, Watts) |
| Unlock sequence | Write `0xB937 = 6` before writing `0xB938` |

---

## Automation example — time-based limit

```yaml
- alias: "Limit export at noon"
  trigger:
    - platform: time
      at: "12:00:00"
  action:
    - service: input_number.set_value
      target:
        entity_id: input_number.solar_power_limit
      data:
        value: 15000

- alias: "Full power after 3pm"
  trigger:
    - platform: time
      at: "15:00:00"
  action:
    - service: input_number.set_value
      target:
        entity_id: input_number.solar_power_limit
      data:
        value: 18500
```

---

## Credits & References

- **PCAPdroid** by emanuele-f — Android network capture without root  
  https://github.com/emanuele-f/PCAPdroid
- **huawei-sun2000-modbus** by wlcrs — Huawei inverter Modbus register map  
  https://github.com/wlcrs/huawei-sun2000-modbus

---

## License

MIT — do whatever you want, no warranty.
