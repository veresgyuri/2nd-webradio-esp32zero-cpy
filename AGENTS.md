# AGENTS.md  

This is a high-level overview for AI agents, AI orchestrator.

> For detailed agent behavior, see `.copilot-instructions.md`

## Goal
Generate working CircuitPython code for an ESP32-based low-cost DIY webradio project.

## Principles
- Prefer simple, readable, reliable solutions.
- Respect existing project structure.  

## Behavior
- Choose the easiest way to work first.
- Follow the rules of `.copilot-instructions.md` for coding

## Output
- Provide complete, usable code by default.
- If modifying existing code, change only what is necessary.

## Hardware Stack
- `ESP32-S3-Zero` - Main board  
- `MAX98357a` - Audio DAC / I2S  
- `EC11` - Rotary encoder with push button  
- `Display` - 128*32 OLED / SSD1306  

## Where to find things (Map)
- **Main application code:** `code.py`
- **Configuration:** `stations.json` and `settings.toml`
- **CircuitPython and hardware-specific instructions:** Found in `/instructions/`
- **AI Core Execution Rules:** `.copilot-instructions.md`
- **On-Demand AI Skills:** Found in `/skills/` (local)

*Note: For explicit write/read permissions for the files above, refer to `.copilot-instructions.md` Section 3.*  

*Note: Skill-based workflows are optional and on-demand. See `.copilot-instructions.md` section 8 for details and locations.*    
