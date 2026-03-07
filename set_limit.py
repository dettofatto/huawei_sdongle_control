#!/usr/bin/env python3
"""
Huawei SDongle - Imposta limite potenza
Uso: python3 set_limit.py <watt>      -> imposta limite
     python3 set_limit.py status      -> legge stato attuale (JSON)
Esempio: python3 set_limit.py 15000
Range: 5000-18500W (you can change)
"""

import socket, time, hashlib, hmac, struct, secrets, sys, json

HOST     = 'ip.dongle'  # IP Raspberry (o dongle diretto)
PORT     = 6606
PASSWORD = 'Changeme'
MIN_W    = 5000
MAX_W    = 18500

MODE_NAMES = {0: "Unlimited", 1: "Fixed", 6: "Active Scheduling"}

def hmac_sha256(key, data):
    return hmac.new(hashlib.sha256(key.encode()).digest(), data, hashlib.sha256).digest()

def connect():
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    u.sendto(bytes.fromhex('5a5a5a5a00413a04c0a8c802'), (HOST, 6600))
    u.close()
    time.sleep(0.5)

    s = socket.socket(); s.settimeout(5); s.connect((HOST, PORT))

    def sr(data, delay=0.5):
        s.send(data); time.sleep(delay)
        try: return s.recv(4096)
        except: return None

    sr(bytes.fromhex('000100000005642b0e0100'), delay=2.0)
    sr(bytes.fromhex('000200000005642b0e0387'))
    r3 = sr(bytes.fromhex('0003000000056441240100'))
    if not r3: raise Exception("No challenge")
    ic = r3[10:26]

    cc = secrets.token_bytes(16); hp = hmac_sha256(PASSWORD, ic); un = b'installer'
    lb = bytes([len(cc)+1+len(un)+1+len(hp), *cc, len(un), *un, len(hp), *hp])
    lp = struct.pack('>HHHBB', 0x0004, 0, 3+len(lb), 0x64, 0x41) + b'\x25' + lb
    r4 = sr(lp)
    if not r4 or r4[10] != 0: raise Exception("Login failed")

    return s

def rd(s, seq, reg, cnt=1):
    p = struct.pack('>HHHBBHH', seq, 0, 6, 0x64, 0x03, reg, cnt)
    s.send(p); time.sleep(0.4); s.settimeout(2)
    try:
        r = s.recv(4096)
        return int(r[9:9+r[8]].hex(), 16) if r and r[7] == 0x03 else None
    except: return None

def wr(s, seq, reg, val, is32=False):
    if is32:
        p = struct.pack('>HHHBBHHB', seq, 0, 11, 0x64, 0x10, reg, 2, 4) + struct.pack('>I', val)
    else:
        p = struct.pack('>HHHBBHH', seq, 0, 6, 0x64, 0x06, reg, val)
    s.send(p); time.sleep(0.5); s.settimeout(2)
    try:
        r = s.recv(4096)
        return r and r[7] in [0x06, 0x10]
    except: return False

def get_status():
    try:
        s = connect()
        seq = 0x0005
        mode      = rd(s, seq, 0xB937);    seq += 1
        limit     = rd(s, seq, 0xB938, 2); seq += 1
        s.close()
        result = {
            "status": "ok",
            "power_limit_w": limit,
            "mode": mode,
            "mode_name": MODE_NAMES.get(mode, f"Unknown({mode})")
        }
        print(json.dumps(result), flush=True)
        return True
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), flush=True)
        return False

def set_power_limit(watts: int) -> bool:
    if not MIN_W <= watts <= MAX_W:
        print(json.dumps({
            "status": "error",
            "error": f"Valore {watts}W fuori range ({MIN_W}-{MAX_W}W)"
        }), flush=True)
        return False

    try:
        s = connect()
        seq = 0x0005

        # Stato attuale
        current = rd(s, seq, 0xB938, 2); seq += 1
        mode    = rd(s, seq, 0xB937);    seq += 1

        # Scrivi nuovo limite
        if not wr(s, seq, 0xB937, 6):
            raise Exception("Write mode failed")
        seq += 1
        if not wr(s, seq, 0xB938, watts, True):
            raise Exception("Write limit failed")
        seq += 1

        # Verifica
        time.sleep(0.5)
        new_val  = rd(s, seq, 0xB938, 2); seq += 1
        new_mode = rd(s, seq, 0xB937);    seq += 1
        s.close()

        if new_val == watts:
            print(json.dumps({
                "status": "ok",
                "power_limit_w": new_val,
                "power_limit_previous_w": current,
                "mode": new_mode,
                "mode_name": MODE_NAMES.get(new_mode, f"Unknown({new_mode})")
            }), flush=True)
            return True
        else:
            raise Exception(f"Verifica fallita: atteso {watts}W, letto {new_val}W")

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), flush=True)
        try: s.close()
        except: pass
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "status":
        ok = get_status()
    else:
        try:
            watts = int(float(arg))
        except ValueError:
            print(json.dumps({"status": "error", "error": f"'{arg}' non e' un numero valido"}))
            sys.exit(1)
        ok = set_power_limit(watts)

    sys.exit(0 if ok else 1)
