# AGENTS.md

## Goal
Generate working CircuitPython code for an ESP32-based low-cost DIY webradio project.

## Principles
- Prefer simple, reliable solutions.
- Keep code readable and lightweight.
- Respect existing project structure.

## Behavior
- Use relevant files from `instructions/` when hardware is involved.
- Choose the simplest working approach first.

## Output
- Provide complete, usable code by default.
- If modifying existing code, change only what is necessary.  

## Project Structure
- **Running on the ESP32 board (CIRCUITPY drive)**  
`code.py` - The main entry point for the application  
`stations.json` - Configuration file for the radio station list  
`settings.toml` - Secure storage for WiFi credentials (SSID and Password)  
`/lib` - Directory for required CircuitPython library modules  

- **Development only (not deployed to board)**   
`AGENTS.md` - overview (the file currently being read)  
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
`/images` - Project photos and diagrams  
`/archive` - Human-user area only so forbidden folder to Ai  
