# AGENTS.md  

> **🛑 AI AGENT DIRECTIVE: DO NOT USE THIS FILE FOR CODING RULES.**
> All agent rules, file permissions, behaviors, and coding standards are strictly defined in `.copilot-instructions.md`. **Load that file immediately.**

## Project Overview
This project builds a low-cost DIY Internet Web Radio using an ESP32-S3 and CircuitPython.

## Goal
Generate working CircuitPython code.

## Hardware Stack
- `ESP32-S3-Zero` - Main board  
- `MAX98357a` - Audio DAC / I2S  
- `EC11` - Rotary encoder with push button  
- `Display` - 128*32 OLED / SSD1306  

## Where to find things (Map)
- **Main application code:** `code.py`
- **Configuration:** `stations.json` and `settings.toml`
- **Hardware-specific instructions:** Found in `/instructions/`
- **AI Core Execution Rules:** `.copilot-instructions.md`
- **On-Demand AI Skills:** Found in `/skills/`

*Note: For explicit write/read permissions for the files above, refer to `.copilot-instructions.md` Section 3.*

*Note: Skill-based workflows are optional and on-demand. See `.copilot-instructions.md` section 8 for details and locations.*    
