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

# ver 1.0 - 2026-02-19 Működő minimál kód


import time
import board
import wifi
import socketpool
import audiobusio
import audiomp3
import os

VERSION = "1.0 - alls. komm. és kapcs. rajz - 2026-02-19"

# --- Beállítások betöltése a settings.toml-ből ---
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

# 1. WiFi Csatlakozás
print(f"Csatlakozás WiFi-hez: {ssid}...")
try:
    wifi.radio.connect(ssid, password)
    print("WiFi csatlakozva! IP:", wifi.radio.ipv4_address)
except Exception as e:
    print("WiFi hiba:", e)
    while True: pass

# 2. Audio kimenet (I2S) beállítása
try:
    audio = audiobusio.I2SOut(bit_clock=PIN_BCLK, word_select=PIN_LRCK, data=PIN_DIN)
    print("I2S hardver OK.")
except Exception as e:
    print("I2S hiba:", e)
    while True: pass

# 3. Socket és Pool létrehozása
pool = socketpool.SocketPool(wifi.radio)

def play_radio():
    print(f"Csatlakozás a szerverhez: {HOST}:{PORT}")
    sock = None
    try:
        # Kapcsolat nyitása
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.connect((HOST, PORT))
        
        # HTTP kérés küldése kézzel (ez a "nyers" módszer)
        request = f"GET {PATH} HTTP/1.0\r\nHost: {HOST}\r\n\r\n"
        sock.send(bytes(request, "utf-8"))
        
        # --- Fejléc átugrása ---
        # A szerver először szöveges infót küld (HTTP/1.0 200 OK...)
        # Ezt addig kell olvasni, amíg nem találunk egy üres sort (\r\n\r\n)
        print("Fejléc átugrása...")
        buffer = bytearray(1)
        prev_seq = b""
        while True:
            count = sock.recv_into(buffer, 1) # Egy bájtot olvasunk egyszerre
            if count == 0:
                raise Exception("A szerver lezárta a kapcsolatot a fejlécben.")
            
            # Figyeljük a dupla soremelést (ez jelzi a fejléc végét)
            prev_seq += buffer
            if b"\r\n\r\n" in prev_seq:
                break # Megvan a zene eleje!
            
            # Hogy ne teljen meg a memória, csak az utolsó 4 karaktert tároljuk
            if len(prev_seq) > 4:
                prev_seq = prev_seq[-4:]

        print("Zene indítása...")
        
        # Itt adjuk át a nyers socketet a dekódernek
        # Most már közvetlenül a zenét kapja
        mp3_stream = audiomp3.MP3Decoder(sock)
     
        audio.play(mp3_stream)
        
        while audio.playing:
            # Itt fut a zene.
            # Ha megszakad a stream, a 'playing' hamis lesz vagy a sock dob hibát.
            pass
            
    except Exception as e:
        print("Hiba lejátszás közben:", e)
        if sock:
            sock.close()
        time.sleep(3)

# Fő ciklus
while True:
    play_radio()