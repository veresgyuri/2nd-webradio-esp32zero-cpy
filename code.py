# code.py - ESP32-S3-zero (MAX98357A) CircuitPython webrádió - OOP verzió

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
            │            │        0.91" OLED 128x32
            │            │     ┌─────────────────────┐
            |         IO4├─────┤SCL     SSD1306     +├─ 3V3
            │         IO5├─────┤SDA                 -├─ GND
            └────────────┘     └─────────────────────┘                       

************ ver 3.xx - MAIN PROGRAM FLOW ******************

    ┌───────────────────────────────────────────────────────────────┐
    │                           POWER ON (BOOT)                     │
    │  1. OLED init -> "Szia! NET kereses... ver.." (Boot screen)   │
    │  2. Load stations from stations.json                          │
    │  3. Restore station index from NVM                            │
    │  4. Create SocketPool                                         │
    └───────────────────────────────────┬───────────────────────────┘
                                        │
                                        ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                         ensure_wifi()                       │
    │                    ┌─────────────────────────┐              │
    │                    │  WiFi csatlakoztatás    │◄─────────┐   │
    │                    │  TX power = 8.5 dBm     │          │   │
    │                    └───────────┬─────────────┘          │   │
    │                                │                        │   │
    │                    ┌───────────┴───────┐                │   │
    │                    │                   │                │   │
    │               [WiFi OK]            [No WiFi]            │   │
    │                    │                   │                │   │
    │                    │                   └───► 3 s wait ──┘   │
    │                    ▼                                        │
    └─────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                           stream_radio()                    │
    │  1. Socket connect (host:port)                              │
    │  2. Send HTTP GET request                                   │
    │  3. Skip headers (\r\n\r\n)                                 │
    │  4. I2S audio init                                          │
    │  5. Create MP3 decoder + play                               │
    │  6. OLED: show_playback(station_name) - nagybetűs 1 sor     │
    └───────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        PLAYBACK LOOP (while audio.playing)               │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                    controls.handle_input()                        │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │                    ENCODER (tekerés)                        │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                             |                                     │   │
│  │         ┌───────────────────┴───────────────────┐                 │   │
│  │         │                                       │                 │   │
│  │    [NORMÁL MÓDBAN]                        [MENÜ MÓDBAN]           │   │
│  │         │                                       │                 │   │
│  │    ACTION_SWITCH_STATION                  ACTION_MENU_BROWSE      │   │
│  │    - Állomás váltás                       - Kurzor mozgatás       │   │
│  │    - NVM mentés azonnal                   - OLED frissítés        │   │
│  │    - audio.stop() -> break                - Zene FOLYTATÓDIK      │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │                      GOMB (KEY)                             │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                            |                                      │   │
│  │              ┌─────────────┴───────────────┐                      │   │
│  │              │                             │                      │   │
│  │         [RÖVID NYOMÁS]                [HOSSZÚ NYOMÁS]             │   │
│  │          (< 1000ms)                     (>= 1000ms)               │   │
│  │              │                             │                      │   │
│  │    ┌─────────┴─────────────┐               │                      │   │
│  │    │                       │               │                      │   │
│  │ [PLAY MÓDBAN]         [MENÜ MÓDBAN]        │                      │   │
│  │    │                       │               │                      │   │
│  │  ACTION_                ACTION_            │                      │   │
│  │  ENTER_MENU             MENU_SELECT        │                      │   │
│  │  - Belépés menübe       - Kiválasztás      │                      │   │
│  │  - OLED 2 soros         - Kilépés menüből  │                      │   │
│  │  - Zene megy tovább     - NVM mentés       │                      │   │
│  │                         - audio.stop()     │    ACTION_HARD_RESET
│  │                         -> break           │    - NVM[0]=0 állomásra
│  │                                            │    - microcontroller.reset()
│  │                                            │                      │   │
│  │                                            └─────────► HARD RESET │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  time.sleep(0.05) - CPU idle                                             │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                               │
       [stream break]                                  [User switched]
    (manual_switch = False)                          (manual_switch = True)
            │                                               │
            ▼                                               ▼
┌─────────────────────────────┐               ┌─────────────────────────────┐
│     Hiba / Szakadás         │               │     Kézi váltás             │
│                             │               │                             │
│  - display.release()        │               │  - audio.deinit()           │
│  - supervisor.reload()      │               │  - socket.close()           │
│        (SOFT RESET)         │               │  - Új állomás betöltése     │
│                             │               │  - Vissza to ensure_wifi()  │
│         ┌───┴───┐           │               │                             │
│         │       │           │               │         ┌──────┴───────┐    │
│         ▼       ▼           │               │         │              │    │
│    ┌──────────────┐         │               │    [Menüből]       [Tekerés]│
│    │ Újra a BOOT- │         │               │    kiválaszts       váltás  │
│    │  (felülről)  │         │               │         │              │    │
│    └──────────────┘         │               │    NVM mentés      NVM már  │
│                             │               │    az új állomásra mentve   │
└─────────────────────────────┘               └─────────────┬───────────────┘
                                                            │
                                                            ▼
                                              ┌─────────────────────────────┐
                                              │  Következő adó streamelése  │
                                              │  (vissza ensure_wifi()-hez) │
                                              └─────────────────────────────┘


**************************** MENÜ MÓD KIJELZŐ ******************************

┌────────────────────────────────────────────────────────────────────────┐
│                         OLED DISPLAY (128x32)                          │
│                                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                     LEJÁTSZÁSI MÓD (show_playback)                │ │
│  │                                                                   │ │
│  │                    ┌────────────────┐                             │ │
│  │                    │                │                             │ │
│  │                    │   RÁDIÓ 1      │    <- scale=3 (max. 7 chr.) │ │
│  │                    │                │                             │ │
│  │                    └────────────────┘                             │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                         MENÜ MÓD (show_menu)                      │ │
│  │                                                                   │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │ >>> RÁDIÓ 1                       scale=1 maximum 21 chr.    │ │ │
│  │  │ < RÁDIÓ 2 >                                                  │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                   │ │
│  │ Felső sor: aktuálisan játszott állomás (rövidítve, ha kell)       │ │
│  │ Alsó sor: lapozható állomás lista (sorszámmal)    Összes áll.[db] │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘


**************************** ÁLLAPOTGÉP ******************************

                    ┌─────────────────┐
                    │                 │
                    │  NORMÁL MÓD     │◄───────────┐
                    │  (Playback)     │            │
                    │                 │            │
                    └────────┬────────┘            │
                             │                     │
                      Rövid nyomás           Kilépés menüből
                      (ENTER_MENU)         (MENU_SELECT után)
                             │                     │
                             ▼                     │
                    ┌─────────────────┐            │
                    │                 │            │
                    │    MENÜ MÓD     │            │
                    │ (Állomás lista) │────────────┘
                    │                 │
                    └────────┬────────┘
                             │
                     Hosszú nyomás
                   (bármelyik módból)
                             │
                             ▼
                    ┌─────────────────┐
                    │                 │
                    │   HARD RESET    │
                    │  (újraindítás)  │
                    │                 │
                    └─────────────────┘

      
*** https://github.com/veresgyuri/2nd-webradio-esp32zero-cpy """

# ver 0.00 - 2026-02-19 Működő minimál kód -> archived
# ver 1.00 - Procedurális eljárásrend - függvényorientált
# ver 1.01 - NET szakadás kezelése - Soft Reset
# ver 1.02 - WiFi TX PWR korlát | 0,2 sec sleep - proci kimélés
# ver 1.10 - 2026-02-26 stations.json - Szeparált állomáslista
# ver 1.20 - Enkóderes csatornaváltás | CH nr. to NVM (max. 255 chanels)
# ver 1.21 - dprint-DEBUG bevezetés | free RAM monitorozás | PEP 8
# ver 1.22 - Enkóder KEY => NVM - 0 és Hard RESET
# ver 1.30 - 2026-03-03 Refaktorált vezérlés (Procedurális)
# ver 2.00 - 2026-03-16 SSD1306 OLED kijelző integrálva (IO4=SCL, IO5=SDA)
# ver 2.10 - cPy ver. 10.x.x import and init format
# ver 2.11 - Add boot screen | Szia! NET... / version
# ver 2.12 - Add a visual program flow
# ver 2.13 - 2026-03-30 Reducing memory leak when channel change
# ver 3.00 - 2026-03-31 OOP refaktorálás (Object-Oriented Programming)

# --- MODULOK ---
# Standard
import gc  # from 1v21
import json  # from 1v10
import os
import time

# Hardware / core
import audiobusio
import board
import busio
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

# OLED kijelző - from 2v00
import displayio
import i2cdisplaybus
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

# --- KONFIGURÁCIÓ ÉS VERZIÓ ---
VERSION = "3.00 - OOP refaktorálás"
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

# OLED I2C (SSD1306)
PIN_OLED_SCL = board.IO4
PIN_OLED_SDA = board.IO5

# --- SEGÉDFÜGGVÉNYEK ---
def dprint(*args, **kwargs):
    """ Soros monitorra iratás kezelése """
    if DEBUG:
        print(*args, **kwargs)


# --- OSZTÁLYOK ---

class StationManager:
    """ Állomások betöltése és kezelése """
    
    def __init__(self, filename="stations.json"):
        self.filename = filename
        self.stations = []
    
    def load(self):
        """ Állomások betöltése JSON fájlból """
        try:
            with open(self.filename, "r") as f:
                self.stations = json.load(f)
            return self.stations
        except Exception as e:
            dprint("JSON hiba:", e)
            self.stations = []
            return []
    
    def get_station(self, index):
        """ Adott indexű állomás lekérése """
        if 0 <= index < len(self.stations):
            return self.stations[index]
        return None
    
    def count(self):
        """ Állomások száma """
        return len(self.stations)


class WiFiManager:
    """ WiFi kapcsolat kezelése """
    
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
    
    def ensure_connection(self):
        """ WiFi kapcsolat ellenőrzése és felépítése """
        gc.collect()  # 1v21 - Memória karbantartás csatlakozás előtt
        # 1v02 - WiFi adóteljesítmény korlát 8,5 dBm-re (7mW vs. 100mW)
        wifi.radio.tx_power = 8.5

        if wifi.radio.connected:
            # 1v02
            dprint(f"Beállított WiFi teljesítmény: {wifi.radio.tx_power} dBm")
            dprint(f"Szabad memória: {gc.mem_free()} byte")
            dprint(f"CPU hőmérséklet: {microcontroller.cpu.temperature:.1f} °C")
            dprint(f"WiFi kapcsolódva: {self.ssid}...")  # 1v02
            return True

        dprint(f"Csatlakozás: {self.ssid}...")
        try:
            wifi.radio.connect(self.ssid, self.password)
            dprint("WiFi SIKERES! IP:", wifi.radio.ipv4_address)
            return True
        except Exception as e:
            dprint("WiFi hiba:", e)
            return False


class AudioPlayer:
    """ I2S Audio és MP3 dekóder kezelése """
    
    def __init__(self):
        self.audio = None
        self.mp3_stream = None
    
    def init(self):
        """ I2S Audio busz indítása """
        try:
            self.audio = audiobusio.I2SOut(
                bit_clock=PIN_I2S_BCLK,
                word_select=PIN_I2S_LRCK,
                data=PIN_I2S_DIN
            )
            return True
        except Exception as e:
            dprint("I2S Init hiba:", e)
            self.audio = None
            return False
    
    def play(self, sock):
        """ MP3 stream lejátszása a socket-ből """
        if not self.audio:
            return False
        
        try:
            self.mp3_stream = audiomp3.MP3Decoder(sock)
            self.audio.play(self.mp3_stream)
            return True
        except Exception as e:
            dprint("MP3 play hiba:", e)
            return False
    
    def is_playing(self):
        """ Ellenőrzi, hogy megy-e a lejátszás """
        if self.audio:
            return self.audio.playing
        return False
    
    def stop(self):
        """ Lejátszás megállítása """
        if self.audio:
            try:
                self.audio.stop()
            except:
                pass
    
    def deinit(self):
        """ Audio erőforrások felszabadítása """
        if self.audio:
            try:
                self.audio.stop()
                self.audio.deinit()
            except:
                pass
            self.audio = None
        
        if self.mp3_stream:
            try:
                self.mp3_stream.deinit()
            except:
                pass
            self.mp3_stream = None


class Display:
    """ OLED kijelző kezelése (SSD1306, 128x32) """
    
    def __init__(self):
        self.text_area = None
    
    def init(self):
        """ OLED kijelző inicializálása """
        displayio.release_displays()  # Felszabadítás - minden esetre!

        try:
            # I2C busz (IO4=SCL, IO5=SDA)
            i2c = busio.I2C(scl=PIN_OLED_SCL, sda=PIN_OLED_SDA)

            # CircuitPython 10.x - közvetlen hívás, nincs try-except
            display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)

            # SSD1306 létrehozás (128x32)
            display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

            # Szöveg címke - INDULÁSI KÉPERNYŐ (Boot screen) from 2v11
            # A VERSION stringből levágjuk az első 4 karaktert (pl. "2.10")
            boot_text = f"Szia!  NET kereses...\nversion: {VERSION[:4]}"

            # scale=2 és line_spacing=1.0 kell ahhoz, hogy 2 sor kiférjen a 32 px magas kijelzőn
            self.text_area = label.Label(
                terminalio.FONT, text=boot_text, scale=1, line_spacing=1.7)
            self.text_area.x = 2
            self.text_area.y = 8
            display.root_group = self.text_area

            dprint("OLED init OK")
            return True
        except Exception as e:
            dprint("OLED init hiba:", e)
            return False
    
    def update(self, station_name):
        """ OLED kijelző frissítése az állomás nevével """
        if self.text_area:
            # Ha még a boot képernyő kisebb betűméretén (2) vagyunk,
            # visszaállítjuk nagyra (3) az adó nevéhez!
            if self.text_area.scale == 1:
                self.text_area.scale = 3
                self.text_area.y = 20  # 1 soros nagybetűhöz középre igazítva

            self.text_area.text = station_name
    
    def release(self):
        """ I2C busz felszabadítása """
        displayio.release_displays()


class Controls:
    """ Rotary encoder és gomb kezelése """
    
    def __init__(self):
        self.encoder = None
        self.key = None
        self.last_position = 0
        self.last_key_state = True
    
    def setup(self):
        """ Létrehozza és visszaadja a vezérlő objektumokat (Encoder, Key) """
        # Enkóder
        self.encoder = rotaryio.IncrementalEncoder(PIN_ENC_S1, PIN_ENC_S2)

        # Gomb (KEY)
        self.key = digitalio.DigitalInOut(PIN_ENC_KEY)
        self.key.direction = digitalio.Direction.INPUT
        self.key.pull = digitalio.Pull.UP  # bár van külső felhúzó ellenállás

        return self.encoder, self.key
    
    def handle_input(self, stations_len, current_index):
        """
        Kezeli a felhasználói beavatkozást (Tekerés vagy Gombnyomás).
        Visszatérési érték: (new_index: int, switched: bool, hard_reset: bool)
        Ha switched=True, akkor csatornaváltás történt.
        Ha hard_reset=True, akkor hard reset kell.
        """
        new_index = current_index
        switched = False
        hard_reset = False

        # 1. ENKÓDER FIGYELÉSE
        position = self.encoder.position
        if position != self.last_position:
            # Váltás történt
            new_index = position % stations_len

            # NVM Mentés azonnal
            microcontroller.nvm[0] = new_index
            dprint(f"Váltás -> Mentve NVM-be: {new_index}")

            self.last_position = position  # Pozíció frissítése
            switched = True  # Jelezzük, hogy váltani kell

        # 2. GOMB (KEY) FIGYELÉSE (Hard Reset funkció)
        try:
            current_key_state = self.key.value
        except Exception:
            current_key_state = True  # Hiba esetén "nem nyomott"-nak vesszük

        # Észlelés: True -> False átmenet (Lefutó él = Nyomás)
        if (not current_key_state) and self.last_key_state:
            # Debouncing (Pergésmentesítés)
            t0 = time.monotonic()
            stable = False
            while (time.monotonic() - t0) < KEY_DEBOUNCE_S:
                if self.key.value:  # Ha felengedik menet közben
                    stable = False
                    break
                stable = True

            if stable and (not self.key.value):
                dprint("KEY lenyomva: NVM törlés és HARD RESET...")
                try:
                    microcontroller.nvm[0] = 0
                except Exception as e:
                    dprint("NVM hiba:", e)

                time.sleep(0.1)  # Biztonsági szünet
                hard_reset = True

        self.last_key_state = current_key_state

        return new_index, switched, hard_reset
    
    def sync_position(self, current_index):
        """ Enkóder pozíció szinkronizálása az aktuális állomáshoz """
        self.encoder.position = current_index
        self.last_position = current_index


class WebRadio:
    """ Fő osztály - összefogja az összes komponenst """
    
    def __init__(self):
        # Komponensek
        self.station_manager = StationManager()
        self.wifi_manager = WiFiManager(SSID, PASSWORD)
        self.audio_player = AudioPlayer()
        self.display = Display()
        self.controls = Controls()
        
        # Állapot
        self.current_index = 0
        self.pool = None
    
    def init_hardware(self):
        """ Hardverek inicializálása """
        dprint("\n" f"--- ESP32-S3 WebRadio {VERSION} ---")
        self.controls.setup()
        self.display.init()
    
    def load_stations(self):
        """ Állomások betöltése """
        stations = self.station_manager.load()
        if not stations:
            dprint("KRITIKUS HIBA: Nincs állomáslista!")
            while True:
                time.sleep(1)
        return stations
    
    def restore_nvm(self):
        """ NVM (Memória) visszaállítása """
        saved_index = microcontroller.nvm[0]
        if saved_index >= self.station_manager.count():
            saved_index = 0
            microcontroller.nvm[0] = 0
        self.current_index = saved_index
        dprint(f"Indítás a {self.current_index}. csatornán...")
    
    def init_network(self):
        """ Hálózat előkészítése """
        self.pool = socketpool.SocketPool(wifi.radio)
    
    def stream_radio(self, station_data):
        """ 
        Kapcsolódás, Pufferelés, Lejátszás.
        A vezérlést átadja a controls.handle_input metódusnak.
        """
        sock = None
        manual_switch = False

        host = station_data['host']
        port = station_data['port']
        path = station_data['path']
        name = station_data['name']

        try:
            dprint(f"Adó: {name}")
            self.display.update(name)  # 2v00 - OLED kiírás

            # 4/1. Socket létrrehozása és kapcsolódás
            sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))

            # 4/2. HTTP Kérés
            request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
            sock.send(bytes(request, "utf-8"))

            # 4/3. Fejléc átugrása (Javított, típusbiztos 1v31)
            buffer = bytearray(1)
            prev = bytearray()

            while True:
                # 1 bájtot olvasunk a bufferbe
                n = sock.recv_into(buffer, 1)

                # Ha a szerver lezárta a kapcsolatot
                if n == 0:
                    raise Exception("Socket lezárt (Remote end closed)")

                # Hozzáfűzzük az előzményekhez
                prev += buffer

                # Keressük a dupla sortörést (\r\n\r\n)
                if b"\r\n\r\n" in prev:
                    break

                # Csak az utolsó 4 bájtot tároljuk, hogy ne fogyjon a memória
                if len(prev) > 4:
                    prev = prev[-4:]

            # 5. Audio hardver és dekóder indítása
            if not self.audio_player.init():
                return False  # Hardver hiba -> Reload

            if not self.audio_player.play(sock):
                return False  # MP3 play hiba -> Reload

            dprint(">>> LEJÁTSZÁS INDULT <<<")
            dprint(f"Szabad RAM: {gc.mem_free()} byte")

            # Enkóder szinkronizálása az aktuális állomáshoz (hogy ne ugorjon egyet induláskor)
            self.controls.sync_position(self.current_index)

            # 6. LEJÁTSZÁSI CIKLUS + VEZÉRLÉS
            while self.audio_player.is_playing():
                # Itt hívjuk meg a kiszervezett vezérlő logikát
                new_index, switched, hard_reset = self.controls.handle_input(
                    self.station_manager.count(), self.current_index
                )
                
                # Hard reset esetén
                if hard_reset:
                    microcontroller.reset()  # HARD RESET - Innen nincs visszatérés
                
                # Ha True-val tér vissza, a felhasználó váltott -> Kilépünk a ciklusból
                if switched:
                    self.current_index = new_index
                    manual_switch = True
                    self.audio_player.stop()
                    break

                # CPU pihentetése a hurokban
                time.sleep(0.05)

        except Exception as e:
            dprint("Stream hiba / Szakadás:", e)
            manual_switch = False  # Ez hiba volt, nem kézi váltás

        finally:
            # Takarítás
            self.audio_player.deinit()
            if sock:
                sock.close()

        return manual_switch
    
    def run(self):
        """ Fő program ciklus """
        # 1. Hardverek inicializálása
        self.init_hardware()

        # 2. Állomások betöltése
        self.load_stations()

        # 3. NVM (Memória) visszaállítása
        self.restore_nvm()

        # 4. Hálózat előkészítése
        self.init_network()

        # 5. Végtelen ciklus
        while True:
            if self.wifi_manager.ensure_connection():
                # Kiválasztjuk az aktuális állomást
                station = self.station_manager.get_station(self.current_index)

                # Indítjuk a streamet
                user_switched = self.stream_radio(station)

                if user_switched:
                    # Ha kézzel váltottunk: Gyors újracsatlakozás (Soft Reset nélkül)
                    dprint("Kézi váltás -> Következő adó...")
                    time.sleep(0.5)
                else:
                    # Ha hiba miatt állt le: Teljes újraindítás (Soft Reset)
                    dprint("Hiba / Szakadás -> SOFT RESET...")
                    self.display.release()  # I2C busz felszabadítása 2v00
                    supervisor.reload()

            else:
                dprint("Nincs WiFi... Újrapróbálás 3mp múlva.")
                time.sleep(3)


# --- FŐ PROGRAM ---
if __name__ == "__main__":
    radio = WebRadio()
    radio.run()
