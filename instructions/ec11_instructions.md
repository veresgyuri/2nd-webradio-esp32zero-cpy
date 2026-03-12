---
description: 'EC11 rotary encoder - hardware and PIN usage rules for code generation'
applyTo: '**/*ec11*'
---

# EC-11
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊
<img src="../images/ec11_encoder.png" alt="Rotary enkóder" width="200">  

*English:*
The ​​EC11 rotary encoder is an electromechanical component that converts rotational motion into digital signals. The direction of rotation can be determined from the signals arriving at its two (S1, S2) outputs. It features a built-in (KEY) pushbutton, which is actuated by pressing the rotating shaft axially. External pull-up resistors are connected to the three digital outputs. Debouncing of the contacts is performed by capacitors. The circuit requires a power supply of 5V (3V3) and GND for operation.
*Magyar:*
Az EC-11 forgó jeladó egy elektromechanikus szerkezet, amely a forgó mozgást digitális jellé alakítja. A forgatás iránya a két (S1, S2) kimenetre érkező jelekből meghatározható. Rendelkezik egy beépített (KEY) nyomógombbal, amit a forgató tengely hosszirányú megnyomásval lehet működtetni. A három digitális kimenetre külső felhúzó ellenállások vannak kötve. Az érintkezők prellmentesítését kondenzátorok végzik. Az áramkör működéséhez tápfeszültség szükséges 5V (3V3) GND.

### Key Technical Specifications - Főbb műszaki jellemzők
*English:*
- Power Output: It is surprisingly powerful for its size, delivering up to 3.2 Watts into a 4-ohm speaker (at 5V power and 10% THD).
- Voltage Range: It operates on a wide DC voltage range from 2.7V to 5.5V.
- Efficiency: As a Class-D amplifier, it is extremely efficient, making it perfect for portable and battery-powered projects.
- Protection: It features built-in thermal and over-current protection.
- Outputs: The outputs are "Bridge-Tied," meaning they connect directly to the speaker terminals and should never be connected to ground.  
  
*Magyar:*
- Teljesítmény: 3,2 Watt teljesítményt képes leadni egy 4 ohmos hangszórón (5V tápfeszültség és 10% THD mellett).
- Tápfeszültség: Széles tartomány, 2,7V és 5,5V DC között üzemeltethető.
- Hatékonyság: Mivel D-osztályú (Class-D) vezérlővel rendelkezik, rendkívül hatékony, így kiválóan alkalmas hordozható, akkumulátoros projektekhez.
- Védelem: Beépített termikus és túláramvédelemmel van ellátva.
- Kimenet: A kimenetek "Bridge-Tied" (hídba kötött) kialakításúak, ami azt jelenti, hogy közvetlenül a hangszóróhoz csatlakoznak, nem pedig a földhöz (GND).


> ⚠️ Az instrukció forrásai:
> - https://www.mouser.com/datasheet/2/15/EC11-1370808.pdf?srsltid=AfmBOorc9aECW_k3qs_R8w5l8OX6pCvFJBU6klEIUNfVBmqe6s65-T20
> - https://modulshop.hu/ec-11-rotary-encoder-modul
---
## NECESSARY DATA FOR THE AGENT
### PIN Reference
Dedicated pins

| PIN    | Function                     |
| ------ | ---------------------------- |
| 5V     | Power input 2.5V to 5.5VDC   |
| GND    | System ground                |
| S1     | Rotary - A direction         |
| S2     | Gain select                  |
| DIN    | Data in                      |          
| BCLK   | Bit Clock                    |
| LRC    | Left/Right Clock             |

*Notes:*
This device does not require a Master Clock (MCLK); if your controller provides one, it can remain disconnected


### GAIN (PIN)
Manages the amplification levels.

- 15dB: 100K resistor between GAIN and GND.
- 12dB: GAIN connected directly to GND.
- 9dB: Unconnected (Default).
- 6dB: GAIN connected directly to Vin.
- 3dB: 100K resistor between GAIN and Vin.

*Notes:*
The system defaults to 9dB if left floating.


### SD / MODE (PIN)
A multi-functional pin for power management and channel selection.


- Shutdown: Connect to GND (voltage < 0.16V) to disable the chip.
- Stereo Mix (L+R)/2: Default mode for the breakout (via internal/external resistors).
- Right Channel only: Voltage between 0.77V and 1.4V.
- Left Channel only: Voltage higher than 1.4V

### Analog Output
Speaker Output (+ / -): Bridge-Tied Load (BTL) terminals.
Critical Constraint: These must be connected directly to the speaker. They alternate polarity and carry a 330kHz PWM signal; they must never be connected to ground or used as a pre-amplifier input.

