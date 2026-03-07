import socket, time, hashlib, hmac, struct, secrets, sys

HOST = '192.168.200.1'
PASSWORD = 'changeme'

if len(sys.argv) < 2 or not sys.argv[1].isdigit():
    print('Uso: python3 set_limit.py <watt>')
    sys.exit(1)

WATTS = int(sys.argv[1])

hmac_sha256 = lambda k, d: hmac.new(hashlib.sha256(k.encode()).digest(), d, hashlib.sha256).digest()

def attempt(watts):
    u = socket.socket(2, 2)
    u.sendto(bytes.fromhex('5a5a5a5a00413a04c0a8c802'), (HOST, 6600))
    u.close()
    time.sleep(0.5)

    s = socket.socket()
    s.settimeout(5)
    s.connect((HOST, 6606))

    def sr(data, delay=0.5):
        s.send(data); time.sleep(delay)
        try: return s.recv(4096)
        except: return None

    def rd(reg, cnt=1):
        global seq
        p = struct.pack('>HHHBBHH', seq, 0, 6, 0x64, 0x03, reg, cnt)
        s.send(p); seq += 1; time.sleep(0.4); s.settimeout(2)
        try:
            r = s.recv(4096)
            return int(r[9:].hex(), 16) if r and r[7] == 0x03 else None
        except: return None

    def wr(reg, val, is32=False):
        global seq
        if is32:
            p = struct.pack('>HHHBBHHB', seq, 0, 11, 0x64, 0x10, reg, 2, 4) + struct.pack('>I', val)
        else:
            p = struct.pack('>HHHBBHH', seq, 0, 6, 0x64, 0x06, reg, val)
        s.send(p); seq += 1; time.sleep(0.5); s.settimeout(2)
        try:
            r = s.recv(4096)
            return r and r[7] in [0x06, 0x10]
        except: return False

    try:
        sr(bytes.fromhex('000100000005642b0e0100'), delay=2.0)
        sr(bytes.fromhex('000200000005642b0e0387'))
        r3 = sr(bytes.fromhex('0003000000056441240100'))

        if not r3 or len(r3) < 26:
            return None, "handshake fallito"

        ic = r3[10:26]
        cc = secrets.token_bytes(16)
        hp = hmac_sha256(PASSWORD, ic)
        un = b'installer'
        lb = bytes([len(cc)+1+len(un)+1+len(hp), *cc, len(un), *un, len(hp), *hp])
        sr(struct.pack('>HHHBB', 0x0004, 0, 3+len(lb), 0x64, 0x41) + b'\x25' + lb)

        global seq
        seq = 0x0005

        wr(0xb937, 6)
        wr(0xb938, watts, True)
        time.sleep(0.5)

        return rd(0xb938, 2), None

    except Exception as e:
        return None, str(e)
    finally:
        try: s.close()
        except: pass

seq = 0x0005
for tentativo in range(1, 6):
    val, err = attempt(WATTS)
    if val == WATTS:
        print(f'{{"power_limit_w": {val}, "status": "OK", "tentativi": {tentativo}}}')
        sys.exit(0)
    reason = err if err else f"letto {val}W invece di {WATTS}W"
    print(f'{{"warning": "Tentativo {tentativo}/5 fallito: {reason}"}}', file=sys.stderr, flush=True)
    time.sleep(5)  # pausa generosa tra tentativi per smaltire TIME_WAIT

print(f'{{"error": "Fallito dopo 5 tentativi"}}')
sys.exit(1)
