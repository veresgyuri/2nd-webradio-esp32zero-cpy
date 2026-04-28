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
**Hardware modules:**
- `ESP32-S3-Zero` - Main board  
- `MAX98357a` - Audio DAC / I2S  
- `EC11` - Rotary encoder with button  
- `Display` - 128*32 OLED / SSD1306  

**Writable files (you may edit):**
- `code.py` - Main application  
- `stations.json` - Station configuration  
- `settings.toml` - WiFi credentials  
- `/lib/*` - CircuitPython libraries  

**Read-only files (NEVER modify):**  
- `README.md` - Human documentation  
- `AGENTS.md` - This overview (keep as reference)  
- `/instructions/*.md` - Hardware-specific guidelines  
- `instructions/CircuitPython_instructions.md` - Core OS guidelines  
- `.copilot-instructions.md` - Agent execution rules
- `/images/*` - Visual project assets  
- `/archive/*` - OFF-LIMITS (user-only sandbox)  
- `/skills/*` - AI agent skill definitions (loaded on-demand)

*Note: Full file permissions detail in `.copilot-instructions.md` section 3.*  
*Note: Skill-based workflows are optional and on-demand. See `.copilot-instructions.md` section 8 for details and locations.*    
