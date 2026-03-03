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
# ver 1.30 - 2026-03-03 Refaktorált vezérlés (Procedurális)

# --- MODULOK ---
# Standard
import gc  # from 1v21
import json  # from 1v10
import os
import time

# Hardware / core
import audiobusio
import board
import microcontroller  # from 1v02 | 1v20 NVM
import rotaryio  # from 1v20
import digitalio  # from 1v22

# System
import supervisor  # from 1v01  

# Network
import socketpool
import wifi

# High-level
import audiomp3

# --- KONFIGURÁCIÓ ÉS VERZIÓ ---
VERSION = "1.30 - Refactored Control"
DEBUG = True  # Ha False - nem ír ki semmit a dprint
KEY_DEBOUNCE_S = 0.05  # Gomb pergésmentesítés ideje (mp)

# --- GLOBÁLIS KONSTANSOK (Hálózat) ---
SSID = os.getenv("CIRCUITPY_WIFI_SSID")
PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# --- PIN DEFINÍCIÓK ---
# Audio I2S
PIN_I2S_BCLK = board.IO8
PIN_I2S_LRCK = board.IO9
PIN_I2S_DIN = board.IO7

# Rotary enkóder & Gomb
PIN_ENC_S1 = board.IO11
PIN_ENC_S2 = board.IO12
PIN_ENC_KEY = board.IO10

# --- GLOBÁLIS ÁLLAPOTVÁLTOZÓK ---
# Ezeket a függvények módosítják, ezért a global scope-ban vannak
last_position = 0
last_key_state = True
current_index = 0

# --- SEGÉDFÜGGVÉNYEK ---
# pylint: disable=invalid-name, global-statement

def dprint(*args, **kwargs):
    """ Soros monitorra iratás kezelése """
    if DEBUG:
        print(*args, **kwargs)

def setup_controls():
    """ Létrehozza és visszaadja a vezérlő objektumokat (Encoder, Key) """
    # Enkóder
    enc = rotaryio.IncrementalEncoder(PIN_ENC_S1, PIN_ENC_S2)
    
    # Gomb (KEY)
    btn = digitalio.DigitalInOut(PIN_ENC_KEY)
    btn.direction = digitalio.Direction.INPUT
    # btn.pull = digitalio.Pull.UP # Ha szükséges, de itt külső felhúzó van
    
    return enc, btn

def handle_user_input(encoder_obj, key_obj, stations_len):
    """
    Kezeli a felhasználói beavatkozást (Tekerés vagy Gombnyomás).
    Visszatérési érték: (new_index_detected: bool)
    Ha True, akkor csatornaváltás történt.
    """
    global last_position, last_key_state, current_index
    
    # 1. ENKÓDER FIGYELÉSE
    position = encoder_obj.position
    if position != last_position:
        # Váltás történt
        current_index = position % stations_len
        
        # NVM Mentés azonnal
        microcontroller.nvm[0] = current_index
        dprint(f"Váltás -> Mentve NVM-be: {current_index}")
        
        last_position = position # Pozíció frissítése
        return True # Jelezzük, hogy váltani kell

    # 2. GOMB (KEY) FIGYELÉSE (Hard Reset funkció)
    try:
        current_key_state = key_obj.value
    except Exception:
        current_key_state = True # Hiba esetén "nem nyomott"-nak vesszük

    # Észlelés: True -> False átmenet (Lefutó él = Nyomás)
    if (not current_key_state) and last_key_state:
        # Debouncing (Pergésmentesítés)
        t0 = time.monotonic()
        stable = False
        while (time.monotonic() - t0) < KEY_DEBOUNCE_S:
            if key_obj.value: # Ha felengedik menet közben
                stable = False
                break
            stable = True
        
        if stable and (not key_obj.value):
            dprint("KEY lenyomva: NVM törlés és HARD RESET...")
            try:
                microcontroller.nvm[0] = 0
            except Exception as e:
                dprint("NVM hiba:", e)
            
            time.sleep(0.1) # Biztonsági szünet
            microcontroller.reset() # HARD RESET - Innen nincs visszatérés
            
    last_key_state = current_key_state
    
    return False # Nem történt csatornaváltás

# --- 0. ADATOK BETÖLTÉSE ---
def load_stations():
    """ Állomások betöltése JSON fájlból """
    try:
        with open("stations.json", "r") as f:
            return json.load(f)
    except Exception as e:
        dprint("JSON hiba:", e)
        return []

# --- 1. WiFi KEZELÉS ---
def ensure_wifi():
    """ WiFi kapcsolat ellenőrzése és felépítése """
    gc.collect() # 1v21 - Memória karbantartás csatlakozás előtt
    # 1v02 - WiFi adóteljesítmény korlát 8,5 dBm-re (7mW vs. 100mW)
    wifi.radio.tx_power = 8.5
    
    if wifi.radio.connected:
        # 1v02
        dprint(f"Beállított WiFi teljesítmény: {wifi.radio.tx_power} dBm")
        dprint(f"Szabad memória: {gc.mem_free()} byte")
        dprint(f"CPU hőmérséklet: {microcontroller.cpu.temperature:.1f} °C")
        dprint(f"WiFi kapcsolódva: {SSID}...")  # 1v02
        # dprint(f"WiFi OK. Pwr: {wifi.radio.tx_power} dBm, RAM: {gc.mem_free()}, CPU: {microcontroller.cpu.temperature:.1f}C")
        # dprint(f"SSID: {SSID}")
        return True
        
    dprint(f"Csatlakozás: {SSID}...")
    try:
        wifi.radio.connect(SSID, PASSWORD)
        dprint("WiFi SIKERES! IP:", wifi.radio.ipv4_address)
        return True
    except Exception as e:
        dprint("WiFi hiba:", e)
        return False

# --- 2. AUDIO INIT ---
def init_audio():
    """ I2S Audio busz indítása """
    try:
        return audiobusio.I2SOut(bit_clock=PIN_I2S_BCLK, word_select=PIN_I2S_LRCK, data=PIN_I2S_DIN)
    except Exception as e:
        dprint("I2S Init hiba:", e)
        return None

# --- 3. STREAM LEJÁTSZÁS ---
def stream_radio(pool, station_data, enc_obj, key_obj):
    """ 
    Kapcsolódás, Pufferelés, Lejátszás.
    A vezérlést átadja a handle_user_input függvénynek.
    """
    global last_position, current_index # Csak olvasáshoz/szinkronhoz kell itt
    
    sock = None
    audio = None
    manual_switch = False
    
    host = station_data['host']
    port = station_data['port']
    path = station_data['path']
    name = station_data['name']
    
    try:
        dprint(f"Adó: {name}")
        
        # 1. Socket létrehozása és kapcsolódás
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # 2. HTTP Kérés
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        sock.send(bytes(request, "utf-8"))
        
        # 3. Fejléc átugrása (Header skipping) - EZ A KRITIKUS RÉSZ, VÁLTOZATLAN!
        buffer = bytearray(1)
        prev_seq = b""
        while True:
            count = sock.recv_into(buffer, 1)
            if count == 0: raise Exception("Socket lezárt (Remote end closed)")
            prev_seq += buffer
            if b"\r\n\r\n" in prev_seq: break
            if len(prev_seq) > 4: prev_seq = prev_seq[-4:]

        # 4. Audio hardver és dekóder indítása
        audio = init_audio()
        if not audio: return False # Hardver hiba -> Reload

        mp3_stream = audiomp3.MP3Decoder(sock)
        audio.play(mp3_stream)
        
        dprint(">>> LEJÁTSZÁS INDULT <<<")
        dprint(f"Szabad RAM: {gc.mem_free()} byte")
        
        # Enkóder szinkronizálása az aktuális állomáshoz (hogy ne ugorjon egyet induláskor)
        enc_obj.position = current_index
        last_position = current_index 

        # 5. LEJÁTSZÁSI CIKLUS + VEZÉRLÉS
        while audio.playing:
            # Itt hívjuk meg a kiszervezett vezérlő logikát
            # Ha True-val tér vissza, a felhasználó váltott -> Kilépünk a ciklusból
            if handle_user_input(enc_obj, key_obj, len(stations)):
                manual_switch = True
                audio.stop()
                break
            
            # CPU pihentetése a hurokban
            time.sleep(0.05)
            
    except Exception as e:
        dprint("Stream hiba / Szakadás:", e)
        manual_switch = False # Ez hiba volt, nem kézi váltás
    
    finally:
        # Takarítás
        if audio:
            audio.stop()
            audio.deinit()
        if sock:
            sock.close()
            
    return manual_switch

# --- FŐ PROGRAM (MAIN LOOP) ---

# 1. Hardverek inicializálása
dprint("\n" f"--- ESP32-S3 WebRadio {VERSION} ---")
encoder, key = setup_controls() # Itt kapjuk meg a hardver objektumokat

# 2. Állomások betöltése
stations = load_stations()
if not stations:
    dprint("KRITIKUS HIBA: Nincs állomáslista!")
    while True: time.sleep(1)

# 3. NVM (Memória) visszaállítása
saved_index = microcontroller.nvm[0]
if saved_index >= len(stations):
    saved_index = 0
    microcontroller.nvm[0] = 0
current_index = saved_index
dprint(f"Indítás a {current_index}. csatornán...")

# 4. Hálózat előkészítése
pool = socketpool.SocketPool(wifi.radio)

# 5. Végtelen ciklus
while True:
    if ensure_wifi():
        # Kiválasztjuk az aktuális állomást
        station = stations[current_index]
        
        # Indítjuk a streamet, átadva a hardver vezérlőket is
        user_switched = stream_radio(pool, station, encoder, key)
        
        if user_switched:
            # Ha kézzel váltottunk: Gyors újracsatlakozás (Soft Reset nélkül)
            dprint("Kézi váltás -> Következő adó...")
            time.sleep(0.5)
        else:
            # Ha hiba miatt állt le: Teljes újraindítás (Soft Reset)
            dprint("Hiba / Szakadás -> SOFT RESET...")
            supervisor.reload()
            
    else:
        dprint("Nincs WiFi... Újrapróbálás 3mp múlva.")
        time.sleep(3)
