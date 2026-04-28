# AGENTS.md  

This is a high-level overview for AI agents.

> For detailed agent behavior, see `.copilot-instructions.md`

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
- See `.copilot-instructions.md` section "Output & Delivery" for validation policies.

## Project Structure

**Writable files (you may edit):**
- `code.py` - Main application  
- `stations.json` - Station configuration  
- `settings.toml` - WiFi credentials  
- `/lib/*` - CircuitPython libraries  

**Read-only files (NEVER modify):**
- `AGENTS.md` - This overview (keep as reference)  
- `.copilot-instructions.md` - Agent execution rules
- `/instructions/*.md` - Hardware-specific guidelines  
- `README.md` - Human documentation  
- `/images/*` - Visual project assets  
- `/archive/*` - OFF-LIMITS (user-only sandbox)

**Hardware modules (reference when coding):**
- `instructions/CircuitPython_instructions.md` - Core OS  
- `instructions/esp32s3zero_instructions.md` - MCU & pinout  
- `instructions/max98357a_instructions.md` - Audio/I2S  
- `instructions/ec11_instructions.md` - Rotary encoder  
- `instructions/128x32_ssd1306_oled_instructions.md` - Display  

*Note: Full file permissions detail in `.copilot-instructions.md` section 3.*  
*Note: Skill-based workflows are optional and on-demand. See `.copilot-instructions.md` section 8 for details and locations.*    
