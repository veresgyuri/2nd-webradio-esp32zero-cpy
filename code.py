# code.py - ESP32-S3-zero (MAX98357A) CircuitPython webrádió - OOP verzió

""" ************ KAPCSOLÁSI RAJZ ******************

             TÁPFESZÜLTSÉG
                 REPL
                  ↓
EC-11            USB-C           MAX98357a
┌┴┐         ┌────┬──┬────┐     ┌──────────┐
 R          │    └──┘ IO7├─────┤DIN   OUT+├-─--┬─────┐
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
# ver 3.10 - 2026-04-03 Menü funkció: rövid nyomásra állomáslista böngészés
# ver 3.11 - játszott/össz db into to display
# ver 3.20 - 2026-04-03 Vizuális visszajelzés gomb lenyomásra -> LISTA
# ver 3.21 - add SSID info to boot display
# ver 3.22 - hibás webcím kezelés (Idle loop)

# --- MODULOK ---
# Standard
import gc
import json
import os
import time

# Hardware / core
import audiobusio
import board
import busio
import microcontroller
import rotaryio
import digitalio

# System
import supervisor

# Network
import socketpool
import wifi

# High-level
import audiomp3

# OLED kijelző
import displayio
import i2cdisplaybus
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

# --- KONFIGURÁCIÓ ÉS VERZIÓ ---
VERSION = "3.22 - Idle loop"
DEBUG = True
KEY_DEBOUNCE_S = 0.05
LONG_PRESS_MS = 1000  # Hosszú nyomás küszöb (ms)

# --- GLOBÁLIS KONSTANSOK (Hálózat) ---
SSID = os.getenv("CIRCUITPY_WIFI_SSID")
PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# --- PIN DEFINÍCIÓK ---
PIN_I2S_BCLK = board.IO8
PIN_I2S_LRCK = board.IO9
PIN_I2S_DIN = board.IO7

PIN_ENC_S1 = board.IO11
PIN_ENC_S2 = board.IO12
PIN_ENC_KEY = board.IO10

PIN_OLED_SCL = board.IO4
PIN_OLED_SDA = board.IO5

# --- SEGÉDFÜGGVÉNYEK ---
def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


# --- OSZTÁLYOK ---

class StationManager:
    """ Állomások betöltése és kezelése """

    def __init__(self, filename="stations.json"):
        self.filename = filename
        self.stations = []

    def load(self):
        try:
            with open(self.filename, "r") as f:
                self.stations = json.load(f)
            dprint(f"Betöltve {len(self.stations)} állomás.")
            return self.stations
        except Exception as e:
            dprint("JSON hiba:", e)
            self.stations = []
            return []

    def get_station(self, index):
        if 0 <= index < len(self.stations):
            return self.stations[index]
        return None

    def get_station_name(self, index):
        """ Csak az állomás nevét adja vissza (menühez) """
        station = self.get_station(index)
        return station['name'] if station else "???"

    def count(self):
        return len(self.stations)


class WiFiManager:
    """ WiFi kapcsolat kezelése """

    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password

    def ensure_connection(self):
        gc.collect()
        wifi.radio.tx_power = 8.5

        if wifi.radio.connected:
            dprint(f"Beállított WiFi teljesítmény: {wifi.radio.tx_power} dBm")
            dprint(f"Szabad memória: {gc.mem_free()} byte")
            dprint(f"CPU hőmérséklet: {microcontroller.cpu.temperature:.1f} °C")
            dprint(f"WiFi kapcsolódva: {self.ssid}...")
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
        if self.audio:
            return self.audio.playing
        return False

    def stop(self):
        if self.audio:
            try:
                self.audio.stop()
            except:
                pass

    def deinit(self):
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
        self.display = None
        self.current_mode = "playback"  # "playback" vagy "menu"
        self.normal_station_name = ""   # Tárolja az eredeti nevet a visszaállításhoz

    def init(self):
        displayio.release_displays()

        try:
            i2c = busio.I2C(scl=PIN_OLED_SCL, sda=PIN_OLED_SDA)
            display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
            self.display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

            boot_text = f"Hello!  {VERSION[:4]} verzio\nkeres...{SSID[:13]}"
            self.text_area = label.Label(
                terminalio.FONT, text=boot_text, scale=1, line_spacing=1.5)
            self.text_area.x = 2
            self.text_area.y = 7
            self.display.root_group = self.text_area

            dprint("OLED init OK")
            return True

        except Exception as e:
            dprint("OLED init hiba:", e)
            return False

    def show_playback(self, station_name):
        """ Lejátszási mód: nagy betű, 1 sor """
        if self.text_area:
            self.current_mode = "playback"
            self.normal_station_name = station_name
            self.text_area.scale = 3
            self.text_area.y = 20
            # Rövidítés, ha túl hosszú (scale3 = 7 karakter)
            if len(station_name) > 7:
                station_name = station_name[:5] + ".."
            self.text_area.text = station_name

    def show_playback_hint(self, station_name):
        """ Lejátszási mód MENU felirattal (lenyomás visszajelzés) """
        if self.text_area:
            self.current_mode = "playback"
            self.text_area.scale = 2
            self.text_area.y = 20
            # scale2 = 10 karakter fér el
            self.text_area.text = f"- LISTA -"

    def restore_playback(self):
        """ Visszaállítja az eredeti lejátszási nézetet """
        if self.text_area and self.normal_station_name:
            self.show_playback(self.normal_station_name)

    def show_menu(self, current_playing_name, browsing_index, station_names, total_stations):
        """
        Menü mód: 2 soros megjelenítés
        - felső sor: aktuálisan játszott állomás (kisebb betű)
        - alsó sor: lapozható lista <- név ->
        """
        if self.text_area and self.display:
            self.current_mode = "menu"

            # Váltás kisebb betűméretre (scale1 = 21 karakter)
            if self.text_area.scale != 1:
                self.text_area.scale = 1
                self.text_area.line_spacing = 1.5

            # Felső sor: [PLAY] + rövidített név
            playing_short = current_playing_name
            if len(playing_short) > 12:
                playing_short = playing_short[:10] + ".."
            top_line = f">>> {playing_short} >>>"

            # Alsó sor: lapozható lista
            browsing_name = station_names[browsing_index] if browsing_index < len(station_names) else "???"
            if len(browsing_name) > 7:
                browsing_name = browsing_name[:5] + ".."

            # Nyilak jelzik a lapozhatóságot
            bottom_line = f"< {browsing_index}.{browsing_name} >  {total_stations} db"

            # Két sor összefűzése új sor karakterrel
            self.text_area.text = f"{top_line}\n{bottom_line}"
            self.text_area.y = 4  # Felső margó

    def release(self):
        displayio.release_displays()


class Controls:
    """ Rotary encoder és gomb kezelése (időméréssel, menü állapottal) """

    # Művelet típusok
    ACTION_NONE = 0
    ACTION_SWITCH_STATION = 1      # Enkóder tekerés normál módban
    ACTION_ENTER_MENU = 2          # Rövid nyomás (belépés menübe) - FELENGEDÉSKOR
    ACTION_MENU_BROWSE = 3         # Enkóder tekerés menüben
    ACTION_MENU_SELECT = 4         # Rövid nyomás menüben (kiválasztás)
    ACTION_HARD_RESET = 5          # Hosszú nyomás
    ACTION_SHOW_MENU_HINT = 6      # MENU felirat mutatása lenyomáskor

    def __init__(self):
        self.encoder = None
        self.key = None
        self.last_position = 0
        self.last_key_state = True
        self.press_start_time = None
        self.in_menu = False
        self.menu_cursor = 0          # Kurzor pozíció a menüben

    def setup(self):
        self.encoder = rotaryio.IncrementalEncoder(PIN_ENC_S1, PIN_ENC_S2)
        self.key = digitalio.DigitalInOut(PIN_ENC_KEY)
        self.key.direction = digitalio.Direction.INPUT
        self.key.pull = digitalio.Pull.UP
        return self.encoder, self.key

    def enter_menu(self):
        """ Belépés menü módba """
        self.in_menu = True
        dprint("Menü mód BE")

    def exit_menu(self):
        """ Kilépés menü módból """
        self.in_menu = False
        dprint("Menü mód KI")

    def is_in_menu(self):
        return self.in_menu

    def get_menu_cursor(self):
        return self.menu_cursor

    def set_menu_cursor(self, cursor):
        self.menu_cursor = cursor

    def sync_position(self, current_index):
        """ Enkóder pozíció szinkronizálása (normál módban) """
        self.encoder.position = current_index
        self.last_position = current_index

    def sync_menu_cursor(self, cursor):
        """ Kurzor szinkronizálása (menüben) """
        self.menu_cursor = cursor

    def handle_input(self, stations_len, current_index):
        """
        Kezeli a felhasználói beavatkozást.
        Visszatérés:
        - action: ACTION_* konstans
        - value: kiegészítő érték (új index vagy kurzor pozíció)
        - hard_reset: ha True, azonnali hard reset kell
        """
        new_index = current_index
        action = self.ACTION_NONE
        hard_reset = False
        # 1. ENKÓDER FIGYELÉSE
        position = self.encoder.position

        if position != self.last_position:
            delta = position - self.last_position
            self.last_position = position

            if self.in_menu:
                # Menü módban: kurzor mozgatása
                new_cursor = self.menu_cursor + delta
                # Ciklikus léptetés
                if new_cursor >= stations_len:
                    new_cursor = 0
                elif new_cursor < 0:
                    new_cursor = stations_len - 1

                self.menu_cursor = new_cursor
                action = self.ACTION_MENU_BROWSE
                dprint(f"Menü kurzor: {self.menu_cursor}")
            else:
                # Normál módban: állomás váltás
                new_index = (current_index + delta) % stations_len
                # NVM mentés azonnal (csak normál módban!)
                microcontroller.nvm[0] = new_index
                dprint(f"Váltás -> Mentve NVM-be: {new_index}")
                action = self.ACTION_SWITCH_STATION

        # 2. GOMB (KEY) FIGYELÉSE (időméréssel + azonnali visszajelzés)
        try:
            current_key_state = self.key.value
        except Exception:
            current_key_state = True

        # LENYOMÁS érzékelése (True -> False)
        if (not current_key_state) and self.last_key_state:
            # Eltároljuk a lenyomás időpontját
            self.press_start_time = time.monotonic()
            dprint("Gomb LENYOMVA")

            # Azonnali vizuális visszajelzés (ha nem vagyunk menüben)
            if not self.in_menu:
                action = self.ACTION_SHOW_MENU_HINT
                dprint("MENU jelzés megjelenítve")

        # FELENGEDÉS érzékelése (False -> True)
        elif current_key_state and (not self.last_key_state):
            if self.press_start_time is not None:
                press_duration_ms = (time.monotonic() - self.press_start_time) * 1000
                self.press_start_time = None

                if press_duration_ms >= LONG_PRESS_MS:
                    # Hosszú nyomás -> Hard Reset
                    dprint(f"Hosszú nyomás: {press_duration_ms:.0f}ms -> HARD RESET")
                    try:
                        microcontroller.nvm[0] = 0
                    except Exception as e:
                        dprint("NVM hiba:", e)
                    hard_reset = True
                    action = self.ACTION_HARD_RESET
                else:
                    # Rövid nyomás
                    dprint(f"Rövid nyomás: {press_duration_ms:.0f}ms")
                    if self.in_menu:
                        # Menüben: kiválasztás
                        action = self.ACTION_MENU_SELECT
                        dprint("Menüben kiválasztás")
                    else:
                        # Normál módban: belépés menübe
                        action = self.ACTION_ENTER_MENU
                        dprint("Belépés menübe")

        self.last_key_state = current_key_state

        # Érték visszaadása (új index vagy kurzor)
        value = new_index if not self.in_menu else self.menu_cursor

        return action, value, hard_reset


class WebRadio:
    """ Fő osztály - összefogja az összes komponenst """

    def __init__(self):
        self.station_manager = StationManager()
        self.wifi_manager = WiFiManager(SSID, PASSWORD)
        self.audio_player = AudioPlayer()
        self.display = Display()
        self.controls = Controls()

        self.current_index = 0
        self.pool = None
        self.stations = []          # Állomások listája
        self.menu_cursor_backup = 0  # Backup menü kurzor (kilépéskor visszaállítás)
        self.hint_shown = False      # Ha a MENU jelzés aktív

    def init_hardware(self):
        dprint("\n" + "=" * 40)
        dprint(f"--- ESP32-S3 WebRadio {VERSION} ---")
        dprint("=" * 40)
        self.controls.setup()
        self.display.init()

    def load_stations(self):
        self.stations = self.station_manager.load()
        if not self.stations:
            dprint("KRITIKUS HIBA: Nincs állomáslista!")
            while True:
                time.sleep(1)
        return self.stations

    def restore_nvm(self):
        saved_index = microcontroller.nvm[0]
        if saved_index >= self.station_manager.count():
            saved_index = 0
            microcontroller.nvm[0] = 0
        self.current_index = saved_index
        dprint(f"Indítás a {self.current_index}. csatornán: {self.station_manager.get_station_name(self.current_index)}")

    def init_network(self):
        self.pool = socketpool.SocketPool(wifi.radio)

    def _get_station_names(self):
        """ Állomásnevek listájának lekérése (menühöz) """
        return [s['name'] for s in self.stations]

    def stream_radio(self, station_data):
        """
        Kapcsolódás, Pufferelés, Lejátszás.
        Visszatérés: manual_switch (True=felhasználó váltott, False=hiba)
        """
        sock = None
        manual_switch = False
        menu_exit_with_select = False
        selected_station_index = self.current_index

        host = station_data['host']
        port = station_data['port']
        path = station_data['path']
        name = station_data['name']

        try:
            dprint(f"Adó: {name}")
            self.display.show_playback(name)

            # Socket és kapcsolódás
            sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))

            # HTTP kérés
            request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
            sock.send(bytes(request, "utf-8"))

            # Fejléc átugrása
            buffer = bytearray(1)
            prev = bytearray()
            while True:
                n = sock.recv_into(buffer, 1)
                if n == 0:
                    raise Exception("Socket lezárt (Remote end closed)")
                prev += buffer
                if b"\r\n\r\n" in prev:
                    break
                if len(prev) > 4:
                    prev = prev[-4:]

            # Audio indítás
            if not self.audio_player.init():
                return False
            if not self.audio_player.play(sock):
                return False

            dprint(">>> LEJÁTSZÁS INDULT <<<")
            dprint(f"Szabad RAM: {gc.mem_free()} byte")

            # Enkóder szinkronizálás
            self.controls.sync_position(self.current_index)
            self.hint_shown = False

            # --- LEJÁTSZÁSI CIKLUS + VEZÉRLÉS ---
            while self.audio_player.is_playing():
                action, value, hard_reset = self.controls.handle_input(
                    self.station_manager.count(), self.current_index
                )

                # Hard reset
                if hard_reset:
                    microcontroller.reset()

                # MENU jelzés lenyomáskor (vizuális visszajelzés)
                if action == self.controls.ACTION_SHOW_MENU_HINT and not self.controls.is_in_menu():
                    self.display.show_playback_hint(
                        self.station_manager.get_station_name(self.current_index)
                    )
                    self.hint_shown = True
                    continue  # Ne csináljunk mást, csak frissítsük a kijelzőt

                # Normál módban: állomás váltás
                if action == self.controls.ACTION_SWITCH_STATION and not self.controls.is_in_menu():
                    self.current_index = value
                    manual_switch = True
                    self.audio_player.stop()
                    dprint(f"Váltás állomásra: {self.current_index}")
                    break

                # Belépés menübe (rövid nyomás normál módban, felengedéskor)
                elif action == self.controls.ACTION_ENTER_MENU:
                    # Ha volt MENU jelzés, távolítsuk el
                    if self.hint_shown:
                        self.display.restore_playback()
                        self.hint_shown = False
                    self.controls.enter_menu()
                    # Kurzor inicializálása az aktuális állomásra
                    self.controls.set_menu_cursor(self.current_index)
                    # Frissítjük a kijelzőt a menü nézetre
                    station_names = self._get_station_names()
                    self.display.show_menu(
                        self.station_manager.get_station_name(self.current_index),
                        self.current_index,
                        station_names,
                        len(station_names)
                    )
                    dprint("Menü megnyitva")

                # Menüben: böngészés (enkóder tekerés)
                elif action == self.controls.ACTION_MENU_BROWSE and self.controls.is_in_menu():
                    # Frissítjük a kijelzőt az új kurzor pozícióval
                    station_names = self._get_station_names()
                    current_playing = self.station_manager.get_station_name(self.current_index)
                    self.display.show_menu(
                        current_playing,
                        self.controls.get_menu_cursor(),
                        station_names,
                        len(station_names)
                    )
                    dprint(f"Menü böngészés: {station_names[self.controls.get_menu_cursor()]}")

                # Menüben: kiválasztás (rövid nyomás)
                elif action == self.controls.ACTION_MENU_SELECT and self.controls.is_in_menu():
                    selected_station_index = self.controls.get_menu_cursor()
                    self.controls.exit_menu()
                    menu_exit_with_select = True
                    manual_switch = True
                    self.audio_player.stop()
                    dprint(f"Menü kiválasztás: {selected_station_index}")
                    break

                # CPU pihentetés
                time.sleep(0.05)

            # Menüből kiválasztással léptünk ki
            if menu_exit_with_select and selected_station_index != self.current_index:
                self.current_index = selected_station_index
                microcontroller.nvm[0] = self.current_index
                dprint(f"NVM mentés új állomásra: {self.current_index}")

        except Exception as e:
            dprint("Stream hiba / Szakadás:", e)
            # Ha menüben voltunk, lépjünk ki belőle
            if self.controls.is_in_menu():
                self.controls.exit_menu()
            manual_switch = False

        finally:
            self.audio_player.deinit()
            if sock:
                sock.close()
            # Ha menüben maradtunk és nem történt kiválasztás, lépjünk ki
            if self.controls.is_in_menu():
                self.controls.exit_menu()
                # Visszaállítjuk a lejátszási nézetet
                self.display.restore_playback()
            # Ha csak a MENU jelzés volt aktív, távolítsuk el
            elif self.hint_shown:
                self.display.restore_playback()
                self.hint_shown = False

        return manual_switch

    def run(self):
        """ Fő program ciklus """
        self.init_hardware()
        self.load_stations()
        self.restore_nvm()
        self.init_network()

        while True:
            if self.wifi_manager.ensure_connection():
                station = self.station_manager.get_station(self.current_index)
                if station is None:
                    dprint("Hiba: Érvénytelen állomás index!")
                    self.current_index = 0
                    microcontroller.nvm[0] = 0
                    continue

                user_switched = self.stream_radio(station)

                if user_switched:
                    dprint("Kézi váltás -> Következő adó...")
                    time.sleep(0.5)
                else:
                    dprint("Hiba / Hibás webcím -> Enkóder forgatással kilépés!")
                    # Idle loop: enkóder forgatásra kilépés
                    reset_countdown = 2  # 1 másodperc (0.5s * 2)
                    while reset_countdown > 0:
                        action, value, _ = self.controls.handle_input(
                            self.station_manager.count(), self.current_index
                        )
                        if action == self.controls.ACTION_SWITCH_STATION:
                            dprint("Enkóder forgatás detektálva -> Kilépés")
                            self.current_index = value
                            break
                        time.sleep(0.5)
                        reset_countdown -= 1

                    # Ha nem történt kilépés, akkor soft reload
                    dprint("Soft reset - supervisor.reload()...")
                    self.display.release()
                    supervisor.reload()
            else:
                dprint("Nincs WiFi... Újrapróbálás 3mp múlva.")
                time.sleep(3)


# --- FŐ PROGRAM ---
if __name__ == "__main__":
    radio = WebRadio()
    radio.run()