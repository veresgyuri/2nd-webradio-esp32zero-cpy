---
description: '2.4" TFT display modul with rotary encoder - ST7789 hardware and usage rules for code generation'
applyTo: '**/*st7789*'
---

# 2.4" TFT Display - ST7789 + EC11 Encoder Module + switch button
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊
<img src="../images/st7789_ec11.png" alt="TFT and Encoder Module" width="200">  

*English:* This 2.4-inch TFT display module integrates an ST7789-driven color screen (320×240 RGB) with a 20-pulse rotary encoder (EC11) featuring a push button, plus an additional K0 button. It communicates via SPI bus, making it ideal for menu systems, control panels, dashboards, and parameter adjustment in embedded projects. The display and input elements share a single PCB, drastically reducing wiring complexity. The module can be powered from 3.3V or 5V, but 3.3V logic is recommended for stable operation, especially with ESP32-class controllers.

*Magyar:* Ez a 2,4 hüvelykes TFT kijelzőmodul egy ST7789 vezérlőjű színes kijelzőt (320×240 RGB) egy 20 impulzus/körös, nyomógombos EC11 forgóenkódert és egy külön K0 gombbal integrál. Az SPI buszon keresztül kommunikál, így menürendszerek, vezérlőpanelek, műszerfalak és paraméterállító alkalmazások ideális választása. A kijelző és a beviteli elemek egyetlen nyákra kerültek, ami drámaian leegyszerűsíti a bekötést. A modul 3,3V vagy 5V tápfeszültséggel működhet, de a stabil működés érdekében – különösen ESP32 típusú vezérlők esetén – a 3,3V logikai szint javasolt.

### Key Technical Specifications - Főbb műszaki jellemzők
*English:*
- Display: 2.4 inch diagonal, TFT, 320×240 RGB resolution.
- Controller: ST7789 (SPI interface).
- Encoder: EC11. 20 pulses per revolution, 20 detents (clicks). Built-in push switch (PUSH).
- Additional Button: K0, separate momentary switch (with onboard RC filter: 10k pull-up + 100nF debounce capacitor).
- Supply: VCC 3.3V or 5V DC. Logic level is determined by VCC, but 3.3V logic is advised for reliable SPI communication.
- Backlight: BLK pin – when left unconnected, backlight is **fully enabled** (on). Can be controlled with PWM for dimming.
- Module Dimensions: approx. 78 mm × 42 mm (gyártói adat).

*Magyar:*
- Kijelző: 2,4 col (6 cm) átlójú, TFT, 320×240 RGB felbontás.
- Vezérlő: ST7789 (SPI interfész).
- Enkóder: EC11 típus, 20 impulzus/kör, 20 kattanás. Beépített nyomógomb (PUSH).
- Extra gomb: K0, különálló nyomógomb (onboard RC szűrővel: 10k felhúzó + 100nF kondenzátor).
- Tápellátás: VCC 3,3V vagy 5V DC. A logikai szint a VCC-vel egyezik, de a stabil SPI működéshez a 3,3V logika ajánlott.
- Háttérvilágítás: BLK pin – bekötetlenül a háttérvilágítás **teljesen bekapcsol**. PWM-mel szabályozható.
- Modul mérete: kb. 78 mm × 42 mm (gyártói adat).

### SPI Interface and Display Configuration
*English:*
The display uses 4-wire SPI (SCLK, MOSI, CS, DC). Reset (RES) is also required. The module silkscreen labels `SCL` for SPI clock and `SDA` for SPI data (MOSI) – this is **NOT** I2C.

- Mandatory pins: GND, VCC, SCL (SPI SCK), SDA (SPI MOSI), RES (display reset), DC (data/command select), CS (chip select, active LOW).
- Optional: BLK (backlight). If left unconnected, backlight stays on. To control brightness, connect to a PWM-capable pin.
- The typical 320×240 resolution can be used in portrait (default) or landscape (`setRotation(1)`). The ST7789 driver handles RGB 5-6-5 color (16-bit) natively.

*Magyar:*
A kijelző 4 vezetékes SPI-t használ (SCLK, MOSI, CS, DC). A reset (RES) vezeték is szükséges. A modul felirata szerint `SCL` az SPI órajel, `SDA` az SPI adat (MOSI) – ez **NEM** I2C.

- Kötelező pinek: GND, VCC, SCL (SPI SCK), SDA (SPI MOSI), RES (kijelző reset), DC (adat/parancs kiválasztás), CS (chip select, aktív LOW).
- Opcionális: BLK (háttérvilágítás). Bekötetlenül a háttérvilágítás folyamatosan világít. Fényerőszabályzáshoz PWM képes pinre kell kötni.
- A 320×240 felbontás álló (alapértelmezett) vagy fekvő (`setRotation(1)`) tájolásban használható. Az ST7789 vezérlő natív módon kezeli az RGB 5-6-5 színmélységet (16 bit).

> ⚠️ Az instrukció forrásai:
> - https://modulshop.hu/24-tft-kijelzo-ec11-forgoenkoder-modul-3127
> - https://manuals.plus/ae/1005008346811816 (gyártói termékmanual)

---
## NECESSARY DATA FOR THE AGENT
### PIN Reference
Aliases in brackets are common names on silkscreen or in libraries.

| PIN    | Function                     | Aliases (typical usage)          |
| ------ | ---------------------------- | -------------------------------- |
| GND    | System ground                |                                  |
| VCC    | Power input 3.3V or 5V DC    | (VDD)                            |
| SCL    | SPI Clock                    | (SCK, CLK) – **NOT I2C**         |
| SDA    | SPI Data (MOSI)              | (MOSI, DIN) – **NOT I2C**        |
| RES    | Display reset                | (RST)                            |
| DC     | Data / Command select        | (A0, D/C)                        |
| CS     | Chip select (active LOW)     | (SS, SSEL)                       |
| BLK    | Backlight control            | (LED) – optional, PWM dimming    |
| A      | Encoder phase A              | (CLK)                            |
| B      | Encoder phase B              | (DT)                             |
| PUSH   | Encoder push button          | (SW, ENC_SW)                     |
| K0     | Extra button                 | (KEY0, USER_BTN)                 |

*Notes:*
- **Pull-up resistors:** All encoder/gpio pins (A, B, PUSH, K0) require pull-ups. Most microcontrollers can enable internal pull-ups (`INPUT_PULLUP`). The K0 line has an onboard 10k pull-up and 100nF debounce capacitor, but internal pull-up is still safe.
- **Debouncing:** The EC11 encoder is mechanical – **mandatory** debouncing (software delay, state machine, or edge filtering). The K0 button is already hardware-debounced (RC filter), but a short software debounce (e.g., 15 ms) is still recommended.
- **Backlight default:** If `BLK` is not connected, the backlight is fully on. Do not leave `BLK` floating if you need to turn it off; instead, drive it LOW (or use PWM).
- **Display reset:** The `RES` pin must be pulsed LOW then HIGH during initialization (min. 10 µs low pulse).

### Encoder and Button Configuration
The EC11 encoder produces quadrature signals on A and B. Typical logic:
- On every state change of A, read B to determine direction: if B = HIGH when A rises → clockwise; if B = LOW → counter-clockwise.
- Alternatively, count both edges with a state machine for higher resolution (not needed for most UI menus).
- The PUSH button and K0 button are active LOW when using pull-ups (LOW = pressed, HIGH = released).

### Code Generation Logic & Rules

**1. Hardware Interface – SPI:**
- Always use the hardware SPI peripheral of the target MCU. Do **not** bit-bang SPI for the display, as it requires high clock rates (typically 20–40 MHz on ESP32, lower on 8‑bit AVR).
- Use well-known libraries: `Adafruit_GFX` + `Adafruit_ST7789` (Arduino, PlatformIO) or `TFT_eSPI` (optimized for ESP32). In MicroPython/CircuitPython, use `busio.SPI` and `displayio` or the `st7789` driver.

**2. Display Initialization:**
- Initialize the ST7789 with `width = 240`, `height = 320` (native orientation). Then call `setRotation(1)` for landscape (320×240) if desired.
- The `CS` and `DC` pins must be correctly specified. `RES` pin is required; pulse it LOW for ≥10 µs then HIGH during setup.
- If `BLK` is unused, do not drive it – leave it disconnected. If PWM control is needed, generate a 1‑20 kHz square wave (e.g., `ledcWrite` on ESP32 or `analogWrite` on AVR).

**3. Encoder Reading (Debouncing & Pull-ups):**
- Enable internal pull-ups on `A`, `B`, `PUSH`, `K0` pins.
- **Never** rely on raw pin reads – always debounce. Recommended methods:
  - For high responsiveness: use pin change interrupts on `A` and `B` with a short cooldown (e.g., 800 µs) and read `B` for direction.
  - For simplicity: sample the encoder in the main loop every 1‑5 ms, use a simple state machine (e.g., `rotary` library).
  - For buttons: implement a 15‑30 ms debounce filter (read after stable level). The K0 button has hardware debounce, but still add a short software debounce for safety.
- When using interrupts, declare variables `volatile` and protect shared data with `noInterrupts()` / `interrupts()` or mutexes.

**4. Display Update Strategy:**
- Avoid refreshing the entire screen at high rates. Use partial updates (`fillRect`, `drawBitmap`) to keep UI responsive.
- Use `setTextSize`, `setCursor`, and `print` for menus. For numeric values, store previous value and only overwrite dirty areas if performance is critical.
- The ST7789 is fast – 20 MHz SPI clock works on most 3.3 V microcontrollers. On 5 V logic (e.g., Arduino Uno), use a level shifter or stay at 8 MHz or lower to avoid damage.

**5. Power and Logic Level Considerations:**
- If the host MCU runs at 5 V logic (Arduino Uno/Nano) and the module is powered from 5 V, it might work but can be unreliable. For production, use 3.3 V logic or level shifters.
- When using ESP32 (3.3 V only), power the module's VCC from 3.3 V as well – **do not** apply 5 V.

**6. Known Hardware Details (from manual):**
- The K0 button has an onboard 10 kΩ pull-up resistor and a 100 nF capacitor to GND (RC debounce). Your code does not need to add external pull-ups, but enabling the internal pull-up does no harm.
- The EC11 encoder has no onboard pull-ups – you **must** enable internal pull-ups or add external resistors (e.g., 10 kΩ to VCC).

> **🤖 SYSTEM NOTE FOR THE AI AGENT:** 
> This document defines hardware-specific operational rules and physical constraints. When generating code, **adapt these rules to the specific programming language, framework, and environment requested by the user in the active prompt.** Always use the most idiomatic and efficient approach for the target environment while strictly respecting the hardware characteristics detailed above. Remember: the silkscreen labels `SCL`/`SDA` refer to SPI, not I2C. The backlight is ON by default if BLK is unconnected – do not generate code that drives BLK unless the user explicitly requests brightness control.