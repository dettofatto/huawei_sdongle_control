# Huawei SDongle - Local Power Limit Control via 6606 port

> **Reverse engineered by a surgeon, not a developer.**  
> Protocol discovered via Android pcap capture (PCAPdroid) and Modbus analysis with AI assistance. Use AP dongle wifi directly and port 6606

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.x-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-compatible-41BDF5)

---

## If you are here, you know the issue. Simply read and write on the sdongle.
---

## What it does

Controls and read the **total export power limit** of a Huawei solar installation locally, without cloud, acting directly on the SDongle A-05 wifi gateway (his AP) — not on individual inverters.

- ✅ Acts on **combined total output** — SDongle distributes the limit across all inverters automatically
- ✅ Set power limit from **5000W to 18500W** (adjustable to your installation)
- ✅ Read current status of inverter Master, Slave and Battery 

---


## Requirements

- Huawei SDongle A-05 (tested on firmware `V200R022C10SPC300`)
- or connected directly to sdongle ap (not via your lan)
- or Raspberry Pi (or any Linux box) connected to SDongle WiFi (`SDongleA-HVxxxxxxxxxx`) with NAT/port-forward from LAN → SDongle:

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
Example of results of python3 dongle_read.py:

```
python3 dongle_read.py         
REGISTRO                         |       VALORE | NOTE
=================================================================

=== DONGLE / SISTEMA ===
Inverter Connessi                |      TIMEOUT | addr=40098 sid=1
Potenza Totale Sistema (W)       |      ERR_LEN | raw=001200000003018302
Energia Totale Sistema (kWh)     |      TIMEOUT | addr=40093 sid=1
Stato Cloud                      |         28.0 | 0=offline 1=online

=== INVERTER MASTER (ID 1) ===
Stato Funzionamento              |      TIMEOUT | addr=32089 sid=1
Codice Allarme 1                 |          0.0 | bitmask
Codice Allarme 2                 |          0.0 | bitmask
Temp. Interna (C)                |         45.6 |
Potenza Attiva (W)               |       2508.0 | signed
Potenza Reattiva (VAR)           |          1.0 | signed
Potenza Apparente (VA)           |   65540996.0 |
Power Factor                     |         10.0 | signed
Frequenza Uscita (Hz)            |        49.96 |
Energia Giorno (kWh)             |        14.67 |
Energia Totale (kWh)             |     23020.92 |

=== STRINGHE PV ===
PV1 Tensione (V)                 |        476.8 |
PV1 Corrente (A)                 |         2.81 |
PV2 Tensione (V)                 |        449.3 |
PV2 Corrente (A)                 |         2.87 |
PV3 Tensione (V)                 |          0.0 | se presente
PV3 Corrente (A)                 |          0.0 | se presente

=== LATO AC / GRID ===
Tensione Fase A (V)              |        242.8 |
Tensione Fase B (V)              |        239.7 |
Tensione Fase C (V)              |        241.3 |
Corrente Fase A (A)              |          0.0 | signed
Corrente Fase B (A)              |      TIMEOUT | addr=32073 sid=1
Corrente Fase C (A)              |          0.0 | signed

=== BATTERIA (ID 1) ===
Tipo Batteria                    |          2.0 | 0=nessuna 1=LiIon
PV3 Corrente (A)            11:57 [20/290]  0.0 | se presente                       === LATO AC / GRID ===
Tensione Fase A (V)              |        242.8 |
Tensione Fase B (V)              |        239.7 |
Tensione Fase C (V)              |        241.3 |
Corrente Fase A (A)              |          0.0 | signed
Corrente Fase B (A)              |      TIMEOUT | addr=32073 sid=1
Corrente Fase C (A)              |          0.0 | signed
=== BATTERIA (ID 1) ===
Tipo Batteria                    |          2.0 | 0=nessuna 1=LiIon
Stato Batteria                   |      E$1:[tmux]*                  Thu 03-12 11:57


```
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

- **PCAPdroid** by emanuele-f — Android network capture with root  
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
