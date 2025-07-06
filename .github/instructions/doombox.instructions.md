---
applyTo: '**'
---
Do not create individual readme files, append a log to the readme.md

# GitHub Copilot Instructions - shmegl's DoomBox

## Project Overview
A Doom gaming kiosk that tracks high scores with the winner receiving a free tattoo. Players scan a QR code to fill out a form, triggering the game remotely via webhook/API/MQTT. Developing on a different host and testing changes after pushing and pulling on client.

**Subheader**: "Highest score gets a free tattoo, scan the QR code and fill out the form to play"

## Architecture
- **Kiosk**: Radxa Zero (ARM64) running DietPi/Debian + XFCE
- **Display**: 2048x1536@60hz → 1280x960 desktop → Doom at lower res (scaled up)
- **Game Engine**: dsda-doom in /usr/games/ directory (OpenGL 3.2 or lower requirement)
- **Form**: Static GitHub Pages site
- **Controller**: DualShock 4 (Bluetooth/wired, auto-connect)
- **Communication**: Webhook/API/MQTT triggers from form to kiosk

## Coding Standards

### General Principles
- **Run as root** for simplicity (this is a kiosk environment)
- **No update scripts** - use GitHub updates + rerun setup/uninstall scripts
- **Shell scripts** for system setup and management
- **Python/Node.js** for API/MQTT handling and game coordination
- **Error handling** for network failures and hardware disconnects

### File Naming
- Scripts: `kebab-case.sh`
- Config files: `snake_case.conf` or `kebab-case.json`
- Logs: `YYYY-MM-DD-component.log`

### Code Style
- Shell: Use `set -euo pipefail`, quote variables, check dependencies
- Python: Follow PEP 8, use type hints, handle exceptions gracefully
- JavaScript: Use modern ES6+, async/await, proper error boundaries

## File Structure
```
shmegl-doombox/
├── CHANGELOG.md
├── README.md
├── setup.sh                 # Main installation script
├── uninstall.sh            # Clean removal script
├── src/
│   ├── kiosk-manager.py     # Main kiosk controller
│   ├── score-handler.py     # Score logging and display
│   ├── controller-input.py  # DualShock 4 input handling
│   └── api-listener.py      # Webhook/MQTT listener
├── config/
│   ├── doom.cfg            # lzdoom configuration
│   ├── kiosk.json          # Kiosk settings
│   └── display.conf        # Display configuration
├── scripts/
│   ├── start-doom.sh       # Game launcher
│   ├── show-leaderboard.sh # Display top 10
│   └── test-mode.sh        # Konami code test run
├── web/                    # Static form files for GitHub Pages
│   ├── index.html          # Form page
│   ├── style.css           # Styling
│   └── form-handler.js     # Form submission logic
├── assets/
│   ├── qr-code.png         # Generated QR code
│   └── overlays/           # Score/name overlay graphics
└── logs/
    └── .gitkeep
```

## Key Implementation Notes

### Hardware Constraints
- ARM64 architecture (use appropriate packages)
- Limited RAM (3.7GB total, ~289MB used at idle)
- Fixed resolution pipeline: native → desktop → game scaling

### DualShock 4 Integration
- Implement Konami code: ↑↑↓↓←→←→BA (starts test mode)
- Auto-reconnect on disconnect
- Handle both Bluetooth and wired connections
- Map all game controls + menu navigation

### Game Integration
- Download DOOM.WAD from: `https://archive.org/download/theultimatedoom_doom2_doom.wad/DOOM.WAD%20%28For%20GZDoom%29/DOOM.WAD`
- Use lzdoom with appropriate OpenGL settings
- Overlay player name and current score during gameplay
- Capture final score automatically

### Form & Communication
- Static form hosted on GitHub Pages
- Generate QR codes dynamically for form URL
- Support multiple trigger methods (webhook preferred, MQTT backup)
- Validate player names and handle duplicates

### Error Recovery
- Graceful handling of network outages
- Controller disconnect recovery
- Game crash detection and restart
- Log all events for debugging

## Security Considerations
- Validate all external inputs (player names, API calls)
- Rate limit form submissions
- Sanitize data before display overlays
- Keep controller access restricted to game functions only