# Huawei SDongle - Local Power Limit Control for Home Assistant

> **Reverse engineered by a surgeon, not a developer.**  
> Protocol discovered via Android pcap capture (PCAPdroid) and Modbus analysis with AI assistance. Use AP dongle directly and port 6606

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.x-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-compatible-41BDF5)

---

## Why this exists — the real problem

If you are here, you know the issue. simply read and write on the sdongle.
---

## What it does

Controls and read the **total export power limit** of a Huawei solar installation locally, without cloud, acting directly on the SDongle A-05 gateway — not on individual inverters.

- ✅ Acts on **combined total output** — SDongle distributes the limit across all inverters automatically
- ✅ Works with **any number of inverters** (master + slaves) on the same SDongle
- ✅ Set power limit from **5000W to 18500W** (adjustable to your installation)
- ✅ Read current status (mode, limit) as **JSON**
- ✅ Works **offline** — no Huawei cloud required
- ✅ After we can Integrates with **Home Assistant** via `shell_command` + `command_line` sensor
- ✅ **30-second polling** for real-time status
- ✅ Pairs with a **grid voltage sensor** to prevent inverter shutdown at 253V

---


## Requirements

- Huawei SDongle A-05 (tested on firmware `V200R022C10SPC300`)
- or connected directly to sdongle ap (not via your lan)
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

## Installation (I've removed ha configuration for now)

1. Copy my script in your directory 

```python
HOST     = 'ip.sdongle'  # Or Raspberry Pi LAN IP; or box, or another wifi connected directly to sdongle
PASSWORD = 'changeme'      # SDongle installer password
```

## Usage

### From command line:
```bash
# Set limit to 15kW
python3 set_limit.py 15000

# Read current status
python3 get_limit.py

# Read all data, you must repeat, the dongle is very slow
python3 dongle_read.py


```


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


---

## Credits & References

- **PCAPdroid** by emanuele-f — Android network capture without root  
  https://github.com/emanuele-f/PCAPdroid
- **huawei-sun2000-modbus** by wlcrs — Huawei inverter Modbus register map  
  https://github.com/wlcrs/huawei-sun2000-modbus

---

## License

MIT — do whatever you want, no warranty.

## Tested setup

- SDongle: A-05
- Firmware: V200R022C10SPC300
- Topology: 2 Huawei inverters behind one SDongle
- HA host: Home Assistant OS / Supervised / Container (specify)
- Access path: direct Wi-Fi or LAN NAT via Raspberry Pi

## Security note

Do not expose TCP 6606 or 502 to the internet.
Keep the SDongle on an isolated network.
Use LAN-only forwarding from a trusted host.
