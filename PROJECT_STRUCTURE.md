# DoomBox Project Structure

This document describes the reorganized and simplified DoomBox project structure.

## Directory Structure

```
doombox/
├── src/                          # Main application source code
│   ├── kiosk-manager.py         # Main kiosk application
│   ├── game-launcher.py         # Game launching logic
│   ├── controller-input.py      # Controller management
│   ├── mqtt-client.py           # MQTT integration
│   ├── fallback_video_player.py # Video playback (software)
│   └── hardware_video_player.py # Video playback (hardware)
├── scripts/                      # Utility scripts organized by function
│   ├── mqtt/                    # MQTT-related scripts
│   ├── video/                   # Video optimization scripts
│   ├── system/                  # System monitoring scripts
│   └── controller-manager.sh    # Controller management
├── tests/                        # All test files organized by category
│   ├── mqtt/                    # MQTT testing
│   └── integration/             # Integration testing
├── tools/                        # Standalone utilities
│   ├── mqtt_commands.py         # MQTT command line tool
│   └── webhook.py              # Webhook bridge
├── config/                       # Configuration files
├── assets/                       # Static assets
├── fonts/                        # Font files
├── icons/                        # Icon files
├── logs/                         # Log files
├── vid/                          # Video files
├── web/                          # Web interface files
└── setup.sh                     # Main setup script
```

## Key Changes Made

### 1. Test Organization
- Moved all `test_*.py` files to `tests/` directory
- Organized by category: `mqtt/`, `integration/`
- Removed empty test files
- Created comprehensive test for MQTT game launch

### 2. Script Organization
- Organized `scripts/` by function: `mqtt/`, `video/`, `system/`
- Removed duplicate optimization scripts
- Kept only functional scripts

### 3. Tools Directory
- Created `tools/` for standalone utilities
- Added `mqtt_commands.py` - command line MQTT client
- Moved `webhook.py` from root

### 4. Removed Empty Files
- Deleted empty Python files that were just stubs
- Created functional replacements where needed

## Usage

### Running Tests
```bash
# Test MQTT game launch functionality
./tests/mqtt/test_game_launch.py [broker_host]

# Test MQTT integration
./tests/mqtt/test_mqtt_integration.py

# Test complete integration
./tests/integration/test_integration.py
```

### MQTT Commands
```bash
# Launch a game
./tools/mqtt_commands.py launch "PlayerName" --skill 3

# Stop current game
./tools/mqtt_commands.py stop

# Get status
./tools/mqtt_commands.py status

# Use different broker
./tools/mqtt_commands.py --broker 10.0.0.215 launch "Test"
```

### Controller Management
```bash
# Scan for controllers
./scripts/controller-manager.sh scan

# Pair with controller
./scripts/controller-manager.sh pair MAC_ADDRESS

# Test controller
./scripts/controller-manager.sh test
```

### Starting the Kiosk
```bash
# Full setup and start
./setup.sh

# Just start kiosk
./start-kiosk.sh
```

## Core Components

### Main Application (`src/`)
- `kiosk-manager.py` - Main pygame application, video playback, UI
- `game-launcher.py` - Handles launching dsda-doom with proper config
- `controller-input.py` - DualShock 4 controller management
- `mqtt-client.py` - MQTT communication for remote control

### Configuration (`config/`)
- `config.py` - All application settings and constants

### Scripts (`scripts/`)
- Organized by function for easier maintenance
- MQTT scripts for broker setup and testing
- Video optimization for different hardware
- System monitoring and performance tools

This reorganization makes the project much cleaner and easier to navigate while maintaining all functionality.
