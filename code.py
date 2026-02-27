# code.py - ESP32-S3-zero (MAX98357A) webrádió CircuitPython alatt

""" ************ KAPCSOLÁSI RAJZ ******************

       TÁPFESZÜLTSÉG
           REPL         
            ↓                       
EC-11      USB-C            MAX98357a
┌┴┐     ┌────┬──┬────┐     ┌──────────┐ 
 R      │    └──┘ IO7├─────┤DIN   OUT+├─-─-┬─────┐ 
 O -CH+ ┤IO10     IO8├─────┤BCLK      │    │     🔊
 T -CH- ┤IO11     IO9├─────┤LRC       │   ┌┴┐   8Ω/1W  
 A      │         GND├─────┤GND       │   │ ←--──┘
 R      ┤         3V3├──┬──┤Vin       │   └┬┘56R
 Y      │            │  └──┤Gain  OUT-├─---┘ 1W        
└ ┘     |            │     └──────────┘               
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
# ver 1.20 - 2026-02-26 Encoderes csatornaváltás | CH nr. to NVM  

import time
import board
import wifi
import socketpool
import audiobusio
import audiomp3
import os
import supervisor # from 1v01 
import microcontroller # from 1v02 | 1v20 NVM
import json # from 1v10
import rotaryio

VERSION = "1.20 - NVM Memory | 2026-02-26"

# --- Globális változók ---
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

PIN_BCLK = board.IO8
PIN_LRCK = board.IO9
PIN_DIN  = board.IO7

# Enkóder
encoder = rotaryio.IncrementalEncoder(board.IO11, board.IO12)
last_position = 0

print("\n" f"--- ESP32-S3 WebRadio {VERSION} ---")

# --- 0. Webrádiók ---
def load_stations():
    """ Állomások betöltése """
    try:
        with open("stations.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print("JSON hiba:", e)
        return []

stations = load_stations()
if not stations:
    print("Hiba: Üres vagy hiányzó stations.json!")
    while True: time.sleep(1)

# --- NVM KEZELÉS (Memória beolvasása) ---
# Kiolvassuk az első byte-ot (0. cím)
saved_index = microcontroller.nvm[0]

# Ellenőrzés: Ha a mentett szám nagyobb, mint a lista hossza (vagy szemét van benne), nullázzuk
if saved_index >= len(stations):
    saved_index = 0
    microcontroller.nvm[0] = 0 # Javítjuk a memóriában is

current_index = saved_index
print(f"Visszatérés a {current_index}. állomáshoz...")

# --- 1. WiFi ---
def ensure_wifi():
    """ Ellenőrzi a kapcsolatot, és ha nincs, csatlakozik """ 
    wifi.radio.tx_power = 8.5 # 1v02 - WiFi adóteljesítmény korlát 8,5 dBm-re (7mW vs. 100mW) 
    if wifi.radio.connected:
        print(f"Beállított WiFi teljesítmény: {wifi.radio.tx_power} dBm") # 1v02
        print(f"CPU hőmérséklet: {microcontroller.cpu.temperature:.1f} °C") # 1v02 
        print(f"WiFi kapcsolódva: {ssid}...") # 1v02
        return True
    print(f"Csatlakozás: {ssid}...")
    try:
        wifi.radio.connect(ssid, password)
        print("WiFi OK! IP:", wifi.radio.ipv4_address)
        return True
    except Exception as e:
        print("WiFi hiba:", e)
        return False

# --- 2. Audio ---
def init_audio():
    """ Létrehozza és visszaadja az I2S objektumot """ 
    try:
        return audiobusio.I2SOut(bit_clock=PIN_BCLK, word_select=PIN_LRCK, data=PIN_DIN)
    except Exception as e:
        print("I2S hiba:", e)
        return None

# --- 3. Stream ---
def stream_radio(pool, station_data):
    """ Nem külön host/port/path, hanem egy 'station' objektum """
    global last_position, current_index
    
    sock = None
    audio = None
    manual_switch = False 
    
    host = station_data['host']
    port = station_data['port']
    path = station_data['path']
    name = station_data['name']
    
    try:
        print(f"Adó: {name}")
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        sock.send(bytes(request, "utf-8"))
        
        buffer = bytearray(1)
        prev_seq = b""
        while True:
            count = sock.recv_into(buffer, 1)
            if count == 0: raise Exception("Socket lezárt")
            prev_seq += buffer
            if b"\r\n\r\n" in prev_seq: break
            if len(prev_seq) > 4: prev_seq = prev_seq[-4:]

        audio = init_audio()
        if not audio: return False 

        mp3_stream = audiomp3.MP3Decoder(sock)
        audio.play(mp3_stream)
        
        print(">>> LEJÁTSZÁS... <<<")
        
        # Enkóder szinkronizálás
        encoder.position = current_index
        last_position = current_index

        while audio.playing:
            position = encoder.position
            if position != last_position:
                # Váltás történt
                current_index = position % len(stations)
                
                # --- NVM MENTÉS ---
                # Azonnal beírjuk a memóriába az új számot
                microcontroller.nvm[0] = current_index 
                print(f"Mentve NVM-be: {current_index}")
                
                manual_switch = True
                audio.stop()
                break 
            
            time.sleep(0.05)
            
    except Exception as e:
        print("Hiba stream közben:", e)
        manual_switch = False
    
    finally:
        if audio:
            audio.stop()
            audio.deinit()
        if sock:
            sock.close()
            
    return manual_switch

# --- FŐ PROGRAM ---
pool = socketpool.SocketPool(wifi.radio)

while True:
    if ensure_wifi():
        station = stations[current_index]
        
        user_switched = stream_radio(pool, station)
        
        if user_switched:
            # Ha a felhasználó váltott, gyorsan megyünk tovább
            print("Kézi váltás...")
            time.sleep(0.5)
        else:
            # Ha HIBA volt (NET szakadás) - jöhet a Soft Reset
            # Mivel az NVM-ben benne van az index, ugyanide térünk vissza!
            print("Hiba -> SOFT RESET (Index megőrizve)")
            # time.sleep(1) #1v20 ---- kell ez?
            supervisor.reload() #1v01
            
    else:
        print("Nincs WiFi, újrapróbálás 5mp múlva...")
        time.sleep(5)