## Project Overview
CircuitPython based internet radio running on the ESP32 microcontroller.  
The objective is to implement a low-cost, hobby and DIY web radio.

## Target Environment & Hardware
- Runtime: [CircuitPython 10.1.4](./instructions/CircuitPython_instructions.md)
- Board: [ESP32-S3-zero](./instructions/esp32s3zero_instructions.md)
- Audio: [MAX98357a](./instructions/max98357a_instructions.md) (I2S DAC)
- Display: [0,91" OLED](./instructions/128x32_ssd1306_oled_instructions.md) (SSD1306)
- Control: [EC11](./instructions/ec11_instructions.md) rotary encoder with push button

## Project Structure
- **Running on the ESP32 board (CIRCUITPY drive)**  
`code.py` - The main entry point for the application  
`stations.json` - Configuration file for the radio station list  
`settings.toml` - Secure storage for WiFi credentials (SSID and Password)  
`/lib` - Directory for required CircuitPython library modules  

- **Development only (not deployed to board)**   
`AGENTS.md` - Dedicated overview for the AI coding agents  
`.copilot-instructions.md` - Dedicated context and coding rules for AI coding agents    
`/instructions` - Project-specific rules and hardware interaction logic  
├── `CircuitPython_instructions.md`  
├── `esp32s3zero_instructions.md`  
├── `max98357a_instructions.md`  
├── `ec11_instructions.md`  
└── `128x32_ssd1306_oled_instructions.md`  

Each _instructions.md file consists of two parts - providing instructions for both human and AI agents.

- **Other resources**:  
`README.md` - Human-oriented documentation  
`/images` - Project photos and diagrams (non-code)  
`/archive` - Deprecated or older code versions (ignore for development)  

## Implementation Logic
AI agents must adhere to the following hierarchical instruction set to ensure compatibility:

**1.** Primary rules: follow [.copilot-instructions.md](.copilot-instructions.md) for coding rules.  
**2.** Modular instructions: for hardware specifics, check the relevant file in `/instructions`.    
**3.** Strict compliance: always follow the CODE GENERATION LOGIC sections in instruction files to avoid hardware errors.

## Setup & Deployment
This is a CircuitPython project, no compilation needed.  

- **Deployment:** manual process by the user - do not automate file transfers. The user copies files to the `CIRCUITPY` drive.  
- **Dependency management:** ensure all required libraries are present in the `/lib` folder.  
- **Validation:** monitor the serial REPL output for real-time debugging and messages.  

## Security

- **Credential Safety:** never hardcode WiFi credentials in `code.py` - strictly use `settings.toml`.

