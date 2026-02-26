# code.py - ESP32-S3-zero (MAX98357A) webrádió CircuitPython alatt

""" ************ KAPCSOLÁSI RAJZ ******************

 TÁPFESZÜLTSÉG
     REPL         
      ↓                       
    USB-C            MAX98357a
┌────┬──┬────┐     ┌──────────┐ 
│    └──┘ IO7├─────┤DIN   OUT+├─-─-┬─────┐ 
│         IO8├─────┤BCLK      │    │     🔊
│         IO9├─────┤LRC       │   ┌┴┐   8Ω/1W  
│         GND├─────┤GND       │   │ ←--──┘
│         3V3├──┬──┤Vin       │   └┬┘56R
│            │  └──┤Gain  OUT-├─---┘ 1W        
|            │     └──────────┘               
│  ESP32-S3  │   Gain to 3V3 -> 6 dB
│    zero    │   
│            │   Gain NC -> 9 dB 
│            │   Gain to GND -> 12dB
│            │
└────────────┘
        
*** https://github.com/veresgyuri/2nd-webradio-esp32zero-cpy """

# ver 0.00 - 2026-02-19 Működő minimál kód -> archived
# ver 1.00 - Procedurális eljárásrend - függvényorientált
# ver 1.01 - NET szakadás kezelése - Soft Reset
# ver 1.02 - WiFi TX PWR korlát | 0,2 sec sleep - proci kimélés
# ver 1.10 - 2026-02-26 stations.json - Szeparált állomáslista


import time
import board
import wifi
import socketpool
import audiobusio
import audiomp3
import os
import supervisor  # from 1v01
import microcontroller # from 1v02
import json  # from 1v10

VERSION = "1.10 - JSON lista | 2026-02-26"

# --- Globális konstansok ---
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Pin kiosztás (ESP32-S3 Zero)
PIN_BCLK = board.IO8
PIN_LRCK = board.IO9
PIN_DIN  = board.IO7

print("\n" "--- ESP32-S3 Zero Webrádió (Socket mód) ---")
print("verzió:", VERSION, "\n")

# --- 0. FÜGGVÉNY: Állomások betöltése ---
def load_stations():
    try:
        with open("stations.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print("Hiba a stations.json betöltésekor:", e)
        return []

# Állomások betöltése a memóriába
stations = load_stations()
if not stations:
    print("Nincsenek állomások! Állj le.")
    while True: time.sleep(1)

# Jelenleg fixen az elsőt játsszuk (később itt lesz az index változó az encóderhez)
current_station_index = 0
current_station = stations[current_station_index]

print(f"Kiválasztott adó: {current_station['name']}")

# --- 1. WiFi kezelés ---
def ensure_wifi():
    """Ellenőrzi a kapcsolatot, és ha nincs, csatlakozik."""
    wifi.radio.tx_power = 8.5 # 1v02 - WiFi adóteljesítmény korlátozva 8,5 dBm-re (7mW vs. 100mW)
    if wifi.radio.connected:
        print(f"Beállított WiFi teljesítmény: {wifi.radio.tx_power} dBm") # 1v02
        print(f"WiFi kapcsolódva: {ssid}...") # 1v02
        print(f"CPU hőmérséklet: {microcontroller.cpu.temperature:.1f} °C") # 1v02
        return True
            
    print(f"Csatlakozás WiFi-hez: {ssid}...")
    try:
        wifi.radio.connect(ssid, password)
        print("WiFi csatlakozva! IP:", wifi.radio.ipv4_address)
        return True
    except Exception as e:
        print("WiFi csatlakozási hiba:", e)
        return False

# --- 2. FÜGGVÉNY: Audio hardver (I2S) indítása ---
def init_audio():
    """Létrehozza és visszaadja az I2S objektumot."""
    try:
        return audiobusio.I2SOut(bit_clock=PIN_BCLK, word_select=PIN_LRCK, data=PIN_DIN)
    except Exception as e:
        print("I2S Init Hiba:", e)
        return None

# --- 3. FÜGGVÉNY: Stream lejátszása (Kicsit módosítva a paramétereket) ---
# Most már nem külön host/port/path-t kér, hanem egy 'station' objektumot
def stream_radio(pool, station):
    sock = None
    audio = None
    
    host = station['host']
    port = station['port']
    path = station['path']
    name = station['name']
    
    try:
        print(f"Csatlakozás: {host}:{port}")
        print(f"Webrádió: {name}")
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        sock.send(bytes(request, "utf-8"))
        
        # Fejléc átugrása (Változatlan logika)
        print("Fejléc feldolgozása...")
        buffer = bytearray(1)
        prev_seq = b""
        while True:
            count = sock.recv_into(buffer, 1)
            if count == 0: raise Exception("Szerver bontotta")
            prev_seq += buffer
            if b"\r\n\r\n" in prev_seq: break
            if len(prev_seq) > 4: prev_seq = prev_seq[-4:]

        audio = init_audio()
        if not audio: return

        print(">>> ZENE INDÍTÁSA <<<")
        mp3_stream = audiomp3.MP3Decoder(sock)
        audio.play(mp3_stream)
        
        while audio.playing:
            time.sleep(0.2)
            
    except Exception as e:
        print("Stream hiba:", e)
    
    finally:
        print("Takarítás...")
        if audio:
            audio.stop()
            audio.deinit()
        if sock:
            sock.close()

# --- FŐ PROGRAM (MAIN LOOP) ---
pool = socketpool.SocketPool(wifi.radio)

while True:
    if ensure_wifi():
        # Itt adjuk át a teljes objektumot
        stream_radio(pool, current_station)
        
        # Ha a stream_radio visszatér (megszakadt)
        print("Soft reset...")
        supervisor.reload() #1v01
    else:
        # Ha nincs NET - várunk és újra próbáljuk
        print("Várakozás WiFi-re...")
        time.sleep(5)