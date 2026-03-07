import socket, time, hashlib, hmac, struct, secrets, sys

HOST = '192.168.200.1'
PASSWORD = 'changeme'

hmac_sha256 = lambda k, d: hmac.new(hashlib.sha256(k.encode()).digest(), d, hashlib.sha256).digest()

u = socket.socket(2, 2)
u.sendto(bytes.fromhex('5a5a5a5a00413a04c0a8c802'), (HOST, 6600))
u.close()
time.sleep(0.5)

s = socket.socket(); s.settimeout(5); s.connect((HOST, 6606))

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

sr(bytes.fromhex('000100000005642b0e0100'), delay=2.0)
sr(bytes.fromhex('000200000005642b0e0387'))
r3 = sr(bytes.fromhex('0003000000056441240100'))

if not r3 or len(r3) < 26:
    print('{"error": "handshake fallito"}'); s.close(); sys.exit(1)

ic = r3[10:26]
cc = secrets.token_bytes(16); hp = hmac_sha256(PASSWORD, ic); un = b'installer'
lb = bytes([len(cc)+1+len(un)+1+len(hp), *cc, len(un), *un, len(hp), *hp])
sr(struct.pack('>HHHBB', 0x0004, 0, 3+len(lb), 0x64, 0x41) + b'\x25' + lb)

seq = 0x0005
mode = rd(0xb937)
limit = rd(0xb938, 2)
s.close()

print(f'{{"modalita": {mode}, "power_limit_w": {limit}}}')
