## Project Overview
CircuitPython based internet radio running on the ESP32 microcontroller.  
The objective is to implement a low-cost, hobby and DIY web radio.

## Target Environment & Hardware
- Runtime: [CircuitPython 10.1.4.](./instructions/CircuitPython_instructions.md)
- Board: [ESP32-S3-zero.](./instructions/esp32s3zero_instructions.md)
- Audio: [MAX98357a](./instructions/max98357a_instructions.md) (I2S DAC)
- Display: [0,91" OLED](./instructions/128x32_ssd1306_oled_instructions.md) (SSD1306)
- Control: [EC11](./instructions/ec11_instructions.md) rotary encoder with push button

## Project Structure
`code.py` The main entry point for the application.  
`stations.json` Configuration file for the radio station list.  
`settings.toml` Secure storage for WiFi credentials (SSID and Password).  
`/lib:` Directory for required CircuitPython library modules.  
`/instructions:` Project-specific rules and hardware interaction logic.  
├── `CircuitPython_instructions.md`  
├── `esp32s3zero_instructions.md`  
├── `max98357a_instructions.md`  
├── `ec11_instructions.md`  
└── `128x32_ssd1306_oled_instructions.md`  
`AGENTS.md` Dedicated context and instructions for AI coding agents.  
`.copilot-instructions.md` Coding rules.  

**Other resources**:  
`README.md` Human-oriented documentation.  
`/images:` Project photos and diagrams (non-code).  
`/archive:` Deprecated or older code versions (ignore for development).
    

## Implementation Logic & Instructions
AI agents must adhere to the following hierarchical instruction set to ensure compatibility:

    Primary Rules: After understanding this AGENTS.md file, follow the instructions specified in the .copilot-instructions.md file.
    Modular Instructions: Refer to specific hardware guidance in the /instructions/ folder.
    Strict Compliance: Always prioritize the CODE GENERATION LOGIC sections found within these instruction files to prevent hardware-specific errors.

## Coding Guidelines
Specific AI coding rules, formatting preferences, and behavioral instructions are defined in [.copilot-instructions.md](.copilot-instructions.md).

## Setup & Deployment Commands
As this is a CircuitPython project, no compilation is needed. Agents should follow these steps:

    Deployment: This is a manual process performed by the user. Do not attempt to automate file transfers. The user will manually copy updated files to the root of the CIRCUITPY drive
    Dependency Management: Ensure all required libraries are present in the /lib folder.
    Validation: Monitor the Serial REPL output for real-time debugging and to verify successful WiFi connection and stream initialization.

## Security

    Credential Safety: Never hardcode WiFi credentials in code.py; strictly use settings.toml.
    Context Integrity: Maintain a modular code structure to avoid "context rot" and ensure that AI suggestions remain accurate to the specific hardware constraints.

