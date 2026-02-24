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
        
"""

# ver 0.00 - 2026-02-19 Működő minimál kód
# ver 1.00 - Procedurális eljárásrend - függvényorientált
# ver 1.01 - NET szakadás kezelése - Soft Reset


import time
import board
import wifi
import socketpool
import audiobusio
import audiomp3
import os
import supervisor # for 1v01
# import microcontroller

VERSION = "1.01 - NET szakadáskor soft reset, 2026-02-22"

# --- Globális konstansok ---
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Rádió szerver adatai (szétbontva)

# Kossuth rádió
# https://mr-stream.connectmedia.hu//4736//mr1.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4736/mr1.mp3"

# Dankó rádió
# https://mr-stream.connectmedia.hu//4748//mr7.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4748/mr7.mp3"

# Bartók rádió
# https://mr-stream.connectmedia.hu//4741//mr3.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4741/mr3.mp3"

# Szakcsi rádió - Jazz
# https://mr-stream.connectmedia.hu//4691//mr9.mp3
# HOST = "mr-stream.connectmedia.hu"
# PORT = 80
# PATH = "/4691/mr9.mp3"

# Petőfi rádió
# https://mr-stream.connectmedia.hu//4738//mr2.mp3
HOST = "mr-stream.connectmedia.hu"
PORT = 80
PATH = "/4738/mr2.mp3"

# Katolikus - low mp3
# http://katolikusradio.hu:9000/live_low.mp3
# HOST = "81.0.119.219"
# PORT = 9000
# PATH = "/live_low.mp3"

# Katolikus - világzene
# http://katolikusradio.hu:9000/vilagzene
# HOST = "81.0.119.219"
# PORT = 9000
# PATH = "/vilagzene"

# Katolikus - Jazz, dixie
# http://www.katolikusradio.hu:9000/jazz_dixie
# HOST = "81.0.119.219"
# PORT = 9000
# PATH = "/jazz_dixie"

# Szépvíz FM - Csíkszépvíz
# http://86.123.109.20:8000/;stream.mp3
# HOST = "86.123.109.20"
# PORT = 8000
# PATH = "/;stream.mp3"

# Fun FM - Csíkszereda
# http://82.78.114.176:8000/funfm.mp3
# HOST = "82.78.114.176"
# PORT = 8000
# PATH = "/funfm.mp3"

# Sansz FM
# HOST = "91.82.85.44"
# PORT = 9056
# PATH = "/;stream.mp3"

# Pin kiosztás (ESP32-S3 Zero)
PIN_BCLK = board.IO8
PIN_LRCK = board.IO9
PIN_DIN  = board.IO7

print("--- ESP32-S3 Zero Webrádió (Socket mód) ---")
print("Ver.:", VERSION, "\n")

# --- 1. WiFi kezelés ---
def ensure_wifi():
    """Ellenőrzi a kapcsolatot, és ha nincs, csatlakozik."""
    if wifi.radio.connected:
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
            pass # Itt szól a zene
            
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