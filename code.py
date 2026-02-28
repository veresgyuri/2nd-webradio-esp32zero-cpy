# code.py - ESP32-S3-zero (MAX98357A) webrádió CircuitPython alatt

""" ************ KAPCSOLÁSI RAJZ ******************

             TÁPFESZÜLTSÉG
                 REPL         
                  ↓                       
EC-11            USB-C           MAX98357a
┌┴┐         ┌────┬──┬────┐     ┌──────────┐ 
 R          │    └──┘ IO7├─────┤DIN   OUT+├─-─-┬─────┐ 
 O ── CH+ ──┤IO11     IO8├─────┤BCLK      │    │     🔊
 T ── CH- ──┤IO12     IO9├─────┤LRC       │   ┌┴┐   8Ω/1W  
 A          │         GND├─────┤GND       │   │ ←--──┘
 R ── KEY ──┤IO10     3V3├──┬──┤Vin       │   └┬┘56R
 Y          │            │  └──┤Gain  OUT-├─---┘ 1W        
└ ┘         |            │     └──────────┘               
            │  ESP32-S3  │   Gain to 3V3 -> 6 dB
            │    zero    │   
            │            │   (Gain NC -> 9 dB) 
            │            │   (Gain to GND -> 12dB)
            │            │
            └────────────┘
        
*** https://github.com/veresgyuri/2nd-webradio-esp32zero-cpy """

# ver 0.00 - 2026-02-19 Működő minimál kód -> archived
# ver 1.00 - Procedurális eljárásrend - függvényorientált
# ver 1.01 - NET szakadás kezelése - Soft Reset
# ver 1.02 - WiFi TX PWR korlát | 0,2 sec sleep - proci kimélés
# ver 1.10 - 2026-02-26 stations.json - Szeparált állomáslista
# ver 1.20 - 2026-02-26 Enkóderes csatornaváltás | CH nr. to NVM
# ver 1.21 - dprint-DEBUG bevezetés | free RAM monitorozás | PEP 8
# ver 1.22 - Enkóder KEY => NVM - 0 és Hard RESET

# --- MODULOK ---
# Standard
import gc # from 1.21
import json # from 1v10
import os
import time

# Hardware / core
import audiobusio
import board
import microcontroller # from 1v02 | 1v20 NVM
import rotaryio # from 1.20
import digitalio  # <-- ÚJ: KEY kezeléshez

# System
import supervisor # from 1v01 

# Network
import socketpool
import wifi

# High-level
import audiomp3

# --- KONFIGURÁCIÓ ÉS VERZIÓ ---
VERSION = "1.22 - RESET KEY added"
DEBUG = True  # Ha False - nem ír ki semmit a dprint

# --- GLOBÁLIS KONSTANSOK (Hálózat) ---
SSID = os.getenv("CIRCUITPY_WIFI_SSID")
PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# --- PIN DEFINÍCIÓK ---
# Audio I2S
PIN_I2S_BCLK = board.IO8
PIN_I2S_LRCK = board.IO9
PIN_I2S_DIN  = board.IO7

# Rotary enkóder
PIN_ENC_S1 = board.IO11
PIN_ENC_S2 = board.IO12
PIN_ENC_KEY = board.IO10

# --- SEGÉDFÜGGVÉNY ---
def dprint(*args, **kwargs):
    """ Soros monitorra iratás kezelése """
    if DEBUG:
        print(*args, **kwargs)

# --- HARDVER INICIALIZÁLÁS ---
# Enkóder létrehozása a definiált lábakkal
encoder = rotaryio.IncrementalEncoder(PIN_ENC_S1, PIN_ENC_S2)
last_position = 0

# KEY inicializálás (minimális beállítás: bemenet, NEM használunk belső pull-t)
key = digitalio.DigitalInOut(PIN_ENC_KEY)
key.direction = digitalio.Direction.INPUT
# Ne állítsunk pull-t (panelről van felhúzó): key.pull = None  -> alapból nincs beállítva

# Key állapotok a debouncinghoz
last_key_state = True  # feltételezzük: panel felhúzottság miatt 'unpressed' = True
KEY_DEBOUNCE_S = 0.05  # 50 ms

# --- INDULÁS ---
dprint("\n" f"--- ESP32-S3 WebRadio {VERSION} ---")

# --- 0. Webrádiók ---
def load_stations():
    """ Állomások betöltése """
    try:
        with open("stations.json", "r") as f:
            return json.load(f)
    except Exception as e:
        dprint("JSON hiba:", e)
        return []

stations = load_stations()
if not stations:
    dprint("Hiba: Üres vagy hiányzó stations.json!")
    while True: time.sleep(1)

# --- NVM KEZELÉS (Memória beolvasása) ---
# Kiolvassuk az első byte-ot (0. cím)
saved_index = microcontroller.nvm[0]

# Ellenőrzés: Ha a mentett szám nagyobb, mint a lista hossza (vagy szemét van benne), nullázzuk
if saved_index >= len(stations):
    saved_index = 0
    microcontroller.nvm[0] = 0 # Javítjuk a memóriában is

current_index = saved_index
dprint(f"Visszatérés a {current_index}. állomáshoz...")

# --- 1. WiFi ---
def ensure_wifi():
    """ Takarít, ellenőrzi a kapcsolatot, és ha nincs - csatlakozik """
    gc.collect() # from 1v21 Kényszerített takarítás. 
    wifi.radio.tx_power = 8.5 # 1v02 - WiFi adóteljesítmény korlát 8,5 dBm-re (7mW vs. 100mW) 
    if wifi.radio.connected:
        dprint(f"Beállított WiFi teljesítmény: {wifi.radio.tx_power} dBm") # 1v02
        dprint(f"Szabad memória: {gc.mem_free()} byte")
        dprint(f"CPU hőmérséklet: {microcontroller.cpu.temperature:.1f} °C") # 1v02 
        dprint(f"WiFi kapcsolódva: {SSID}...") # 1v02
        return True
    dprint(f"Csatlakozás: {SSID}...")
    try:
        wifi.radio.connect(SSID, PASSWORD)
        dprint("WiFi OK! IP:", wifi.radio.ipv4_address)
        return True
    except Exception as e:
        dprint("WiFi hiba:", e)
        return False

# --- 2. Audio ---
def init_audio():
    """ Létrehozza és visszaadja az I2S objektumot """ 
    try:
        return audiobusio.I2SOut(bit_clock=PIN_I2S_BCLK, word_select=PIN_I2S_LRCK, data=PIN_I2S_DIN)
    except Exception as e:
        dprint("I2S hiba:", e)
        return None

# --- 3. Stream ---
def stream_radio(pool, station_data):
    """ Nem külön host/port/path, hanem egy 'station' objektum """
    global last_position, current_index, last_key_state
    
    sock = None
    audio = None
    manual_switch = False 
    
    host = station_data['host']
    port = station_data['port']
    path = station_data['path']
    name = station_data['name']
    
    try:
        dprint(f"Adó: {name}")
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
        
        dprint(">>> LEJÁTSZÁS... <<<")
        dprint(f"Szabad memória: {gc.mem_free()} byte")
        
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
                dprint(f"Mentve NVM-be: {current_index}")
                
                manual_switch = True
                audio.stop()
                break 

            # --- KEY kezelése: ha lenyomva -> NVM[0]=0 és hard reset ---
            try:
                current_key_state = key.value  # True = nem nyomott (feltételezve panel pull-up)
            except Exception:
                current_key_state = True  # ha valamiért hiba, feltételezzük nem nyomott

            # Észlelés: True -> False átmenet (nyomás)
            if (not current_key_state) and last_key_state:
                # rövid debouncing
                t0 = time.monotonic()
                stable = False
                while (time.monotonic() - t0) < KEY_DEBOUNCE_S:
                    if key.value:  # ha felengedett, nem stabil nyomás
                        stable = False
                        break
                    stable = True
                if stable and (not key.value):
                    dprint("KEY lenyomva: NVM[0]=0, HARD RESET indul...")
                    try:
                        microcontroller.nvm[0] = 0
                    except Exception as e:
                        dprint("NVM írás hiba:", e)
                    # kis késleltetés, hogy a NVM írás befejeződjön
                    time.sleep(0.05)
                    microcontroller.reset()  # hard reset
                    # execution nem folytatódik, de ha mégis -> break
                    break

            last_key_state = current_key_state

            time.sleep(0.05)
            
    except Exception as e:
        dprint("Hiba stream közben:", e)
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
            dprint("Kézi váltás...")
            time.sleep(0.5)
        else:
            # Ha HIBA volt (NET szakadás) - jöhet a Soft Reset
            # Mivel az NVM-ben benne van az index, ugyanide térünk vissza!
            dprint("Hiba -> SOFT RESET (Index megőrizve)")
            # time.sleep(1) #1v20 ---- kell ez?
            supervisor.reload() #1v01
            
    else:
        dprint("Nincs WiFi, újrapróbálás 5mp múlva...")
        time.sleep(5)
