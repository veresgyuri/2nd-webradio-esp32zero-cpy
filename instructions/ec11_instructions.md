---
description: 'EC11 rotary encoder - hardware and PIN usage rules for code generation'
applyTo: '**/*ec11*'
---

# EC-11
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊
<img src="../images/ec11_encoder.png" alt="Rotary enkóder" width="200">  

*English:*
The ​​EC11 rotary encoder is an (incremental) electromechanical component that converts rotational motion into digital signals. The direction of rotation can be determined from the signals arriving at its two (S1, S2) outputs. It features a built-in (KEY) pushbutton, which is actuated by pressing the rotating shaft axially. External pull-up resistors are connected to the three digital outputs. Debouncing of the contacts is performed by capacitors. The circuit requires a power supply of 5V (3V3) and GND for operation.
*Magyar:*
Az EC-11 forgó jeladó egy (inkrementális elvű) elektromechanikus szerkezet, amely a forgó mozgást digitális jellé alakítja. A forgatás iránya a két (S1, S2) kimenetre érkező jelekből meghatározható. Rendelkezik egy beépített (KEY) nyomógombbal, amit a forgató tengely hosszirányú megnyomásával lehet működtetni. A három digitális kimenetre külső felhúzó ellenállások vannak kötve. Az érintkezők prellmentesítését kondenzátorok végzik. Az áramkör működéséhez tápfeszültség szükséges 5V (3V3) GND.

### Key Technical Specifications - Főbb műszaki jellemzők
*English:*
- Type: Incremental (Quadrature) rotary encoder with integrated momentary push-button.
- Resolution: 20 pulses per 360° rotation (with detents).
- Operating Voltage: 2.5V – 5.5V DC (compatible with 3.3V and 5V logic).
- Output Signals: Two-phase (A and B) square wave signals with 90° phase shift.
- Switch: Normally Open (NO), active LOW when pressed.
- Hardware Features: Built-in pull-up resistors (typically 10kΩ) and RC filter capacitors for basic hardware debouncing.
  
*Magyar:*
- Típus: Inkrementális (kvadratúra) forgó jeladó beépített pillanatnyi nyomógombbal.
- Felbontás: 20 impulzus / 360° fordulat (pozíció-reteszeléssel).
- Üzemi feszültség: 2.5V – 5.5V DC (3.3V és 5V logikai szintekkel kompatibilis).
- Kimeneti jelek: Kétfázisú (A és B) négyszögjel, 90°-os fáziseltolással.
- Kapcsoló: Alaphelyzetben nyitott (NO), lenyomáskor aktív LOW szint.
- Hardveres jellemzők: Beépített felhúzó ellenállások (jellemzően 10kΩ) és RC szűrő kondenzátorok az alapvető prellmentesítéshez.

> ⚠️ Az instrukció forrásai:
> - https://www.mouser.com/datasheet/2/15/EC11-1370808.pdf?srsltid=AfmBOorc9aECW_k3qs_R8w5l8OX6pCvFJBU6klEIUNfVBmqe6s65-T20
> - https://modulshop.hu/ec-11-rotary-encoder-modul
---
## NECESSARY DATA FOR THE AGENT
### PIN Reference
Dedicated pins

| PIN    | Function                         |
| ------ | -------------------------------- |
| GND    | System ground                    |
| S1     | Phase A - Pulses during rotation |
| S2     | Phase B - Pulses during rotation |
| KEY    | Pushbutton switch - active LOW   |          
| 5V     | Power input 2.5V to 5.5VD    |

*Notes:*
S2 is 90° offset from S1

### CODE GENERATION LOGIC & RULES
Direction Detection:
- If S1 transitions from HIGH to LOW, check S2.
- If S2 is HIGH → Clockwise (CW).
- If S2 is LOW → Counter-Clockwise (CCW).

Interrupts:
Use hardware interrupts (external interrupts) on S1 and S2 pins for high-speed rotation tracking to avoid missing steps.

Debouncing:
- Hardware: The PCB includes RC filters (capacitors).
- Software: Use a 5-10ms lockout timer for the KEY (SW) to prevent double-click triggers.

Pull-up Configuration:
- Since the module has physical resistors, configure pins as INPUT (or INPUT_PULLUP as a safety measure).

*Notes:*
Atomic Operations:
- Ensure that the counter variable updated in the Interrupt Service Routine (ISR) is declared as volatile. In the main loop, use atomic blocks to read it if the architecture requires it (e.g., 8-bit AVR).

State Machine Approach:
- For the most robust detection, a state machine (handling all 4 states of the AB signals) is preferred over simple edge detection if the application requires extreme precision.

Rotation Speed:
- The EC11 is a mechanical switch; avoid polling in delay() heavy loops. Always prioritize interrupts or a high-frequency (1ms) timer interrupt for polling.

Button Logic:
- The KEY pin is typically pulled HIGH by the onboard resistor. Coding should look for a FALLING edge or LOW state.


### Implementation Examples
1. C++ (Arduino / ESP32) - Interrupt Driven
#include <Arduino.h>

const int S1_PIN = 2; // CLK
const int S2_PIN = 3; // DT
const int KEY_PIN = 4; // SW

volatile int encoderCount = 0;
unsigned long lastButtonPress = 0;

void IRAM_ATTR handleEncoder() {
    // Ha S1 (A) lefutó él, ellenőrizzük S2 (B) állapotát az irányhoz
    int s2State = digitalRead(S2_PIN);
    if (s2State == HIGH) {
        encoderCount++;
    } else {
        encoderCount--;
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(S1_PIN, INPUT_PULLUP);
    pinMode(S2_PIN, INPUT_PULLUP);
    pinMode(KEY_PIN, INPUT_PULLUP);
    
    // Megszakítás S1 lefutó élére (FALLING)
    attachInterrupt(digitalPinToInterrupt(S1_PIN), handleEncoder, FALLING);
}

void loop() {
    static int lastCount = 0;
    if (encoderCount != lastCount) {
        Serial.printf("Position: %d\n", encoderCount);
        lastCount = encoderCount;
    }

    if (digitalRead(KEY_PIN) == LOW && (millis() - lastButtonPress > 200)) {
        Serial.println("Button Pressed!");
        lastButtonPress = millis();
    }
}


2. CircuitPython - Rotaryio Module
import board
import rotaryio
import digitalio
import time

# Enkóder inicializálása (S1, S2)
encoder = rotaryio.IncrementalEncoder(board.D2, board.D3)

# Gomb inicializálása (KEY)
button = digitalio.DigitalInOut(board.D4)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

last_position = 0

while True:
    # Pozíció lekérdezése
    position = encoder.position
    if position != last_position:
        print(f"Position: {position}")
        last_position = position
    
    # Gombnyomás kezelése szoftveres debouncing-gal
    if not button.value:
        print("Button Pressed!")
        time.sleep(0.2) # Egyszerű várakozás a prellmentesítéshez
