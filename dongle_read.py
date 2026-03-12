import socket, time, hashlib, hmac, struct, secrets

HOST = '192.168.203.1' #ip dongle only directly ap
PASSWORD = 'Changeme"

def hmac_sha256(k, d):
    return hmac.new(hashlib.sha256(k.encode()).digest(), d, hashlib.sha256).digest()

def connect_and_auth():
    s = socket.socket()
    s.settimeout(7)
    u = socket.socket(2, 2)
    u.sendto(bytes.fromhex('5a5a5a5a00413a04c0a8c802'), (HOST, 6600))
    u.close()
    time.sleep(0.5)
    s.connect((HOST, 6606))
    s.send(bytes.fromhex('000100000005642b0e0100')); time.sleep(0.8)
    s.send(bytes.fromhex('000200000005642b0e0387')); time.sleep(0.5)
    r3 = s.recv(4096)
    ic = r3[10:26]
    hp = hmac_sha256(PASSWORD, ic)
    cc = secrets.token_bytes(16)
    un = b'installer'
    lb = bytes([len(cc)+1+len(un)+1+len(hp), *cc, len(un), *un, len(hp), *hp])
    s.send(struct.pack('>HHHBB', 0x0004, 0, 3+len(lb), 0x64, 0x41) + b'\x25' + lb)
    time.sleep(1.5)
    return s

# (Label, addr, count, divisore, slave_id, signed, note)
regs = [
    ("=== DONGLE / SISTEMA ===",        0,     0, 1,    1,   False, ""),
    ("Inverter Connessi",               40098, 1, 1,    1,   False, "numero"),
    ("Potenza Totale Sistema (W)",      40087, 2, 1,    1,   True,  "signed"),
    ("Energia Totale Sistema (kWh)",    40093, 2, 100,  1,   False, ""),
    ("Stato Cloud",                     43005, 1, 1,    1,   False, "0=offline 1=online"),

    ("=== INVERTER MASTER (ID 1) ===",  0,     0, 1,    1,   False, ""),
    ("Stato Funzionamento",             32089, 1, 1,    1,   False, "512=standby 1024=griglia"),
    ("Codice Allarme 1",                32008, 1, 1,    1,   False, "bitmask"),
    ("Codice Allarme 2",                32009, 1, 1,    1,   False, "bitmask"),
    ("Temp. Interna (C)",               32087, 1, 10,   1,   False, ""),
    ("Potenza Attiva (W)",              32080, 2, 1,    1,   True,  "signed"),
    ("Potenza Reattiva (VAR)",          32082, 2, 1,    1,   True,  "signed"),
    ("Potenza Apparente (VA)",          32084, 2, 1,    1,   False, ""),
    ("Power Factor",                    32086, 1, 1000, 1,   True,  "signed"),
    ("Frequenza Uscita (Hz)",           32085, 1, 100,  1,   False, ""),
    ("Energia Giorno (kWh)",            32114, 2, 100,  1,   False, ""),
    ("Energia Totale (kWh)",            32106, 2, 100,  1,   False, ""),

    ("=== STRINGHE PV ===",             0,     0, 1,    1,   False, ""),
    ("PV1 Tensione (V)",                32016, 1, 10,   1,   False, ""),
    ("PV1 Corrente (A)",                32017, 1, 100,  1,   False, ""),
    ("PV2 Tensione (V)",                32018, 1, 10,   1,   False, ""),
    ("PV2 Corrente (A)",                32019, 1, 100,  1,   False, ""),
    ("PV3 Tensione (V)",                32020, 1, 10,   1,   False, "se presente"),
    ("PV3 Corrente (A)",                32021, 1, 100,  1,   False, "se presente"),

    ("=== LATO AC / GRID ===",          0,     0, 1,    1,   False, ""),
    ("Tensione Fase A (V)",             32069, 1, 10,   1,   False, ""),
    ("Tensione Fase B (V)",             32070, 1, 10,   1,   False, ""),
    ("Tensione Fase C (V)",             32071, 1, 10,   1,   False, ""),
    ("Corrente Fase A (A)",             32072, 1, 1000, 1,   True,  "signed"),
    ("Corrente Fase B (A)",             32073, 1, 1000, 1,   True,  "signed"),
    ("Corrente Fase C (A)",             32074, 1, 1000, 1,   True,  "signed"),

    ("=== BATTERIA (ID 1) ===",         0,     0, 1,    1,   False, ""),
    ("Tipo Batteria",                   37000, 1, 1,    1,   False, "0=nessuna 1=LiIon"),
    ("Stato Batteria",                  37002, 1, 1,    1,   False, "0=off 1=standby 2=carica 6=scarica"),
    ("Carica/Scarica (W)",              37001, 2, 1,    1,   True,  "+carica -scarica"),
    ("Tensione Batteria (V)",           37003, 1, 10,   1,   False, ""),
    ("Corrente Batteria (A)",           37021, 1, 10,   1,   True,  "signed"),
    ("SOC (%)",                         37004, 1, 10,   1,   False, ""),
    ("SOH (%)",                         37009, 1, 10,   1,   False, "state of health"),
    ("Temp. Batteria (C)",              37022, 1, 10,   1,   False, ""),
    ("Cicli di Carica",                 37028, 1, 1,    1,   False, ""),
    ("Capacita Max (kWh)",              37066, 2, 100,  1,   False, ""),
    ("Capacita Residua (kWh)",          37019, 2, 100,  1,   False, ""),
    ("Energia Carica Tot (kWh)",        37015, 2, 100,  1,   False, ""),
    ("Energia Scarica Tot (kWh)",       37017, 2, 100,  1,   False, ""),
    ("Potenza Max Carica (W)",          37046, 2, 1,    1,   False, ""),
    ("Potenza Max Scarica (W)",         37048, 2, 1,    1,   False, ""),

    ("=== SMART METER (ID 100) ===",    0,     0, 1,  100,   False, ""),
    ("Potenza Istantanea (W)",          37113, 2, 1,  100,   True,  "+immissione -prelievo"),
    ("Tensione Fase A (V)",             37101, 1, 10, 100,   False, ""),
    ("Tensione Fase B (V)",             37102, 1, 10, 100,   False, ""),
    ("Tensione Fase C (V)",             37103, 1, 10, 100,   False, ""),
    ("Corrente Fase A (A)",             37107, 1, 100,100,   True,  "signed"),
    ("Corrente Fase B (A)",             37108, 1, 100,100,   True,  "signed"),
    ("Corrente Fase C (A)",             37109, 1, 100,100,   True,  "signed"),
    ("Frequenza Rete (Hz)",             37118, 1, 100,100,   False, ""),
    ("Energia Immessa Tot (kWh)",       37119, 2, 100,100,   False, ""),
    ("Energia Prelevata Tot (kWh)",     37121, 2, 100,100,   False, ""),
    ("Potenza Attiva Fase A (W)",       37132, 2, 1,  100,   True,  ""),
    ("Potenza Attiva Fase B (W)",       37134, 2, 1,  100,   True,  ""),
    ("Potenza Attiva Fase C (W)",       37136, 2, 1,  100,   True,  ""),

    ("=== INVERTER SLAVE (ID 2) ===",   0,     0, 1,    2,   False, ""),
    ("Stato Slave",                     32089, 1, 1,    2,   False, ""),
    ("Potenza Attiva Slave (W)",        32080, 2, 1,    2,   True,  "signed"),
    ("Temp. Interna Slave (C)",         32087, 1, 10,   2,   False, ""),
    ("Energia Giorno Slave (kWh)",      32114, 2, 100,  2,   False, ""),
    ("Energia Totale Slave (kWh)",      32106, 2, 100,  2,   False, ""),
    ("PV1 Tensione Slave (V)",          32016, 1, 10,   2,   False, ""),
    ("PV2 Tensione Slave (V)",          32018, 1, 10,   2,   False, ""),
]

RECONNECT_EVERY = 8

print()
print(f"{'REGISTRO':<32} | {'VALORE':>12} | NOTE")
print("=" * 65)

s = None
query_count = 0
tid = 0x0010

try:
    s = connect_and_auth()

    for label, addr, cnt, div, sid, signed, note in regs:

        if addr == 0:
            print(f"\n\033[1;36m{label}\033[0m")
            continue

        if query_count > 0 and query_count % RECONNECT_EVERY == 0:
            s.close()
            time.sleep(1.2)
            s = connect_and_auth()

        tid = (tid + 1) & 0x7FFF
        p = struct.pack('>HHHBBHH', tid, 0, 6, sid, 0x03, addr, cnt)
        s.send(p)
        time.sleep(0.45)

        try:
            r = s.recv(4096)
            expected = 9 + (2 * cnt)
            if r and len(r) >= expected:
                raw = r[9:9+(2*cnt)]
                val = int(raw.hex(), 16)
                if signed:
                    limit = 0x7FFF if cnt == 1 else 0x7FFFFFFF
                    wrap  = 0x10000 if cnt == 1 else 0x100000000
                    if val > limit:
                        val -= wrap
                result = round(val / div, 2)
                print(f"{label:<32} | {result:>12} | {note}")
            else:
                print(f"{label:<32} | {'ERR_LEN':>12} | raw={r.hex()[:40] if r else 'vuoto'}")
        except TimeoutError:
            print(f"{label:<32} | {'TIMEOUT':>12} | addr={addr} sid={sid}")
        except Exception as e:
            print(f"{label:<32} | {'ERRORE':>12} | {e}")

        query_count += 1

finally:
    if s:
        s.close()
