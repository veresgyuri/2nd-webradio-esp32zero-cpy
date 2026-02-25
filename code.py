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


import time
import board
import wifi
import socketpool
import audiobusio
import audiomp3
import os
import supervisor # from 1v01
import microcontroller # from 1v02

VERSION = "1.02 - TX PWR | 0,2 sleep, 2026-02-25"

# --- Globális konstansok ---
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Rádió szerver adatai (szétbontva)

# NAME = "Kossuth rádió"
# https://mr-stream.connectmedia.hu//4736//mr1.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4736/mr1.mp3"

# NAME = "Dankó rádió"
# https://mr-stream.connectmedia.hu//4748//mr7.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4748/mr7.mp3"

# NAME = "Bartók rádió"
# https://mr-stream.connectmedia.hu//4741//mr3.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4741/mr3.mp3"

# NAME = "Szakcsi rádió - Jazz"
# https://mr-stream.connectmedia.hu//4691//mr9.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4691/mr9.mp3"

# NAME = "Petőfi rádió"
# https://mr-stream.connectmedia.hu//4738//mr2.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4738/mr2.mp3"

# NAME = "Katolikus - low mp3"
# http://katolikusradio.hu:9000/live_low.mp3
# HOST = "81.0.119.219"
# PORT = 9000
# PATH = "/live_low.mp3"

# NAME = "Katolikus - világzene"
# http://katolikusradio.hu:9000/vilagzene
# HOST = "81.0.119.219"
# PORT = 9000
# PATH = "/vilagzene"

# NAME = "Katolikus - Jazz, dixie"
# http://www.katolikusradio.hu:9000/jazz_dixie
# HOST = "81.0.119.219"
# PORT = 9000
# PATH = "/jazz_dixie"

NAME = "Szépvíz FM - Csíkszépvíz"
# http://86.123.109.20:8000/;stream.mp3
HOST = "86.123.109.20"
PORT = 8000
PATH = "/;stream.mp3"

# NAME = "Fun FM - Csíkszereda"
# http://82.78.114.176:8000/funfm.mp3
# HOST = "82.78.114.176"
# PORT = 8000
# PATH = "/funfm.mp3"

# NAME = "Sansz FM"
# HOST = "91.82.85.44"
# PORT = 9056
# PATH = "/;stream.mp3"

# Pin kiosztás (ESP32-S3 Zero)
PIN_BCLK = board.IO8
PIN_LRCK = board.IO9
PIN_DIN  = board.IO7

print("\n", "--- ESP32-S3 Zero Webrádió (Socket mód) ---")
print("verzió:", VERSION, "\n")

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

# --- 3. FÜGGVÉNY: Stream lejátszása (A 'munkás' rész) ---
def stream_radio(pool, host, port, path):
    """Csatlakozik a szerverhez és lejátssza a streamet."""
    sock = None
    audio = None
    
    try:
        print(f"Csatlakozás a szerverhez: {host}:{port}")
        print(f"Webrádió: {NAME}")
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        sock.send(bytes(request, "utf-8"))
        
        # Fejléc átugrása
        print("Fejléc feldolgozása...")
        buffer = bytearray(1)
        prev_seq = b""
        while True:
            count = sock.recv_into(buffer, 1)
            if count == 0: raise Exception("Szerver bontotta")
            prev_seq += buffer
            if b"\r\n\r\n" in prev_seq: break
            if len(prev_seq) > 4: prev_seq = prev_seq[-4:]

        # Audio indítása csak akkor, ha már van adat
        audio = init_audio()
        if not audio: return # Ha hardver hiba van, kilépünk

        print(">>> ZENE INDÍTÁSA <<<")
        mp3_stream = audiomp3.MP3Decoder(sock)
        audio.play(mp3_stream)
        
        while audio.playing:
            # pass # Itt szól a zene - 1v01-ig
            time.sleep(0.2) # 200 ms pihenőidő - proci kimélés 1v02
            
    except Exception as e:
        print("Stream hiba:", e)
    
    finally:
        # TAKARÍTÁS (Ez fut le mindig, hiba esetén is)
        print("Takarítás...")
        if audio:
            audio.stop()
            audio.deinit() # Kerregés ellen! (?)
        if sock:
            sock.close()

# --- FŐ PROGRAM (MAIN LOOP) ---
pool = socketpool.SocketPool(wifi.radio)

while True:
    if ensure_wifi():
        # Ha van net, mehet a zene
        stream_radio(pool, HOST, PORT, PATH)
        
        # Ha a stream_radio visszatér (megszakadt)
        print("Soft reset...")
        supervisor.reload() #1v01
        # time.sleep(3) #?
        # microcontroller.reset() # HARD RESET! (?)
    else:
        # Ha nincs NET - várunk és újra próbáljuk
        print("Várakozás WiFi-re...")
        time.sleep(5)