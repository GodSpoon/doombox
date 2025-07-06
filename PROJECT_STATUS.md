# DoomBox - Current Project Status

## 🎮 Project Overview
DoomBox is a kiosk-style gaming system that runs Doom and displays a leaderboard. Players scan a QR code to register, then play Doom to compete for high scores.

## 📋 Current Status

### ✅ Completed Components
- **Kiosk Display Application** (`src/kiosk-manager.py`)
  - Pygame-based fullscreen kiosk interface
  - QR code display for player registration
  - Real-time leaderboard display
  - Video background with Doom demo videos
  - Purple theme with clean UI design
  - SQLite database for score storage

- **Controller Support** (`src/controller-input.py`)
  - DualShock 4 controller management
  - Bluetooth pairing and connection
  - Konami code detection
  - Controller input monitoring

- **Game Launcher** (`src/game-launcher.py`) 
  - dsda-doom integration
  - Player session management
  - Game configuration management
  - Score logging to database

- **System Integration**
  - DietPi autologin configuration
  - Systemd service for kiosk
  - Startup scripts and dependencies

### 🚧 In Progress / Next Steps
- **MQTT Integration** - Ready for server setup
- **Score Processing** - Needs game-to-database integration
- **Web Server** - For remote management

### ⚙️ Hardware Requirements
- **Tested On**: Radxa Zero (ARM-based SBC)
- **OS**: DietPi (Debian-based)
- **Display**: 4:3 aspect ratio (1280x960 optimized)
- **Controllers**: DualShock 4 (Bluetooth)

## 🚀 Setup Instructions

### Prerequisites
```bash
# Install system dependencies
sudo apt update && sudo apt install -y \
    git wget curl unzip \
    python3 python3-pip python3-venv python3-opencv libopencv-dev \
    ffmpeg libavcodec-dev libavformat-dev libswscale-dev \
    dsda-doom doom-wad-shareware sqlite3 \
    bluetooth bluez bluez-tools joystick jstest-gtk \
    feh unclutter xset

# Clone the repository
git clone <repository-url> /opt/doombox
cd /opt/doombox

# Install Python dependencies
pip3 install -r requirements.txt
```

### Controller Setup
dsda-doom controller support is already configured in `/root/.dsda-doom/dsda-doom.cfg`:
```ini
use_joystick 1
joy_left 0
joy_right 1
joy_up 2
joy_down 3
joy_fire 4
joy_use 5
joy_run 6
joy_strafe 7
joy_menu 8
joy_weapon_next 9
joy_weapon_prev 10
```

### DietPi Autologin Setup
For automatic kiosk startup on boot:

```bash
# Configure DietPi autologin
sudo ./configure-dietpi-autologin.sh

# Or manually set in /boot/dietpi.txt:
AUTO_SETUP_AUTOSTART_TARGET_INDEX=7
AUTO_SETUP_AUTOSTART_LOGIN_USER=dietpi
AUTO_SETUP_CUSTOM_SCRIPT_EXEC=1
```

### Manual Testing
```bash
# Test the kiosk display
python3 src/kiosk-manager.py

# Test controller pairing
python3 src/controller-input.py --scan
python3 src/controller-input.py --pair <MAC_ADDRESS>

# Test game launcher
python3 src/game-launcher.py --test
python3 src/game-launcher.py --launch "TestPlayer"
```

## 📁 Project Structure
```
doombox/
├── src/
│   ├── kiosk-manager.py          # Main kiosk application
│   ├── controller-input.py       # Controller management
│   └── game-launcher.py          # Game launching system
├── config/
│   └── config.py                 # Configuration settings
├── fonts/                        # Puffin arcade fonts
├── vid/                          # Doom demo videos
├── web/                          # Web interface files
├── logs/                         # Application logs
├── requirements.txt              # Python dependencies
├── setup.sh                      # Installation script
├── start-kiosk.sh               # Kiosk startup script
├── configure-dietpi-autologin.sh # DietPi autologin setup
└── doombox-kiosk.service        # Systemd service
```

## 🔧 System Services

### Systemd Service
```bash
# Service control
sudo systemctl start doombox-kiosk.service
sudo systemctl stop doombox-kiosk.service
sudo systemctl status doombox-kiosk.service

# View logs
journalctl -u doombox-kiosk.service -f
```

### Manual Control
```bash
# Start kiosk manually
./start-kiosk.sh

# Stop kiosk
pkill -f kiosk-manager.py
```

## 🌐 Network Configuration
- **Form URL**: http://shmeglsdoombox.spoon.rip
- **QR Code**: Generated automatically for player registration
- **MQTT**: Ready for integration (server needed)

## 📊 Database Schema
```sql
-- Scores table
CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    score INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Game sessions table
CREATE TABLE game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    event TEXT NOT NULL,
    exit_code INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 Current Goals
1. **Complete MQTT Integration** - Set up server for remote commands
2. **Score Processing** - Connect game scores to database
3. **Web Management** - Remote control and monitoring
4. **Prize System** - Automated winner notification

## 🔍 Debugging

### Logs
- Kiosk: `/opt/doombox/logs/kiosk.log`
- Controller: `/opt/doombox/logs/controller.log`
- Game: `/opt/doombox/logs/game-launcher.log`
- System: `journalctl -u doombox-kiosk.service`

### Common Issues
1. **Black Screen**: Check display configuration and X11 setup
2. **Controller Not Working**: Verify Bluetooth and jstest
3. **Game Won't Launch**: Check dsda-doom installation and WAD files
4. **Database Errors**: Verify SQLite permissions and paths

## 🚀 Next Phase: MQTT Integration
Ready for server setup on another host to send MQTT commands for:
- Remote game launching
- Score synchronization
- System monitoring
- Prize notifications

The system is now ready for DietPi autologin configuration and MQTT server integration!
