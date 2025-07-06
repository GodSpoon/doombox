# shmegl's DoomBox

**frag4ink**

An interactive promo kiosk built on Radxa Zero that displays a QR code for user registration, launches DOOM with custom player names, tracks high scores, and awards prizes to top players.

## Hardware Requirements

- Radxa Zero SBC (4GB RAM recommended)
- 2048x1536 display (running at 1280x960)
- DualShock 4 controller (Bluetooth or wired)
- Network connectivity (WiFi/Ethernet)

## Software Stack

- **OS**: Dietpi/Debian 12
- **Desktop**: XFCE4
- **Game Engine**: dsda-doom (with lzdoom compatibility wrapper)
- **Backend**: Python 3 with Flask
- **Database**: SQLite
- **Communication**: MQTT (mosquitto)

## Quick Setup

### 1. Clone the Repository on Your Radxa Zero

```bash
# Clone the repository
git clone https://github.com/your-username/doombox.git
cd doombox

# Verify you have all required files
ls -la
# Should show: kiosk.py, setup.sh, config.py, webhook.py, index.html, etc.
```

### 2. Run the Setup Script as Root

```bash
sudo bash setup.sh
```

The setup script will:
- Install all system dependencies (dsda-doom, Python, MQTT, etc.)
- Create Python virtual environment with required packages
- Download DOOM.WAD from archive.org
- Copy all application files from the repository to `/opt/doombox/`
- Create systemd service and startup scripts
- Set up XFCE desktop entries for testing
- Configure auto-login and auto-start options

### 3. Start the Display Server

```bash
# Start X11 for testing
/opt/doombox/start_x_display.sh
```

### 4. Test Components

```bash
# Test dsda-doom directly
/opt/doombox/test_dsda_doom.sh

# Test via lzdoom compatibility wrapper
/opt/doombox/test_doom.sh

# Test the full kiosk application
/opt/doombox/test_kiosk.sh
```

### 5. Pair Your DualShock 4 Controller

```bash
# Use the new consolidated controller management script
./scripts/controller-manager.sh scan
./scripts/controller-manager.sh pair MAC_ADDRESS
./scripts/controller-manager.sh auto-connect
```

### 6. Configure Your Web Form URL

Edit the QR code URL in `/opt/doombox/src/kiosk-manager.py`:
```python
self.form_url = "https://your-username.github.io/doombox-form/"
```

Or update the configuration in `/opt/doombox/config/config.py`:
```python
GITHUB_FORM_URL = "https://your-username.github.io/doombox-form/"
```

### 7. Start the Kiosk Service

```bash
# Enable and start the service
/opt/doombox/start_kiosk_service.sh

# Or manually:
sudo systemctl enable doombox.service
sudo systemctl start doombox.service
```

## Features

### 🎮 Game Integration
- Launches dsda-doom with custom player names & overlay
- Automatic game exit detection and score logging
- lzdoom compatibility wrapper for seamless integration

### 🎯 Controller Support
- DualShock 4 Bluetooth/wired support
- Konami code (`↑↑↓↓←→←→BA`) for test games
- Auto-reconnection on boot

### 📊 Score Tracking
- SQLite database for persistent scores
- Real-time top 10 leaderboard display
- Timestamp tracking for tie-breaking

### 🔗 Remote Integration
- QR code generation for web form
- MQTT support for remote game triggers
- Webhook/API integration ready

---

## Controller Management

### Overview
The DoomBox uses a DualShock 4 controller with advanced pairing and connection management. The system supports both Bluetooth and wired connections with automatic reconnection.

### Quick Controller Setup
```bash
# Scan for controllers
./scripts/controller-manager.sh scan

# Pair a specific controller
./scripts/controller-manager.sh pair MAC_ADDRESS

# Auto-connect to saved controller
./scripts/controller-manager.sh auto-connect

# Check controller status
./scripts/controller-manager.sh status

# Test controller input
./scripts/controller-manager.sh test
```

### Controller Features
- **Konami Code Support**: ↑↑↓↓←→←→BA triggers test mode
- **Auto-reconnection**: Automatically connects to paired controllers on startup
- **Multiple pairing methods**: 5 different approaches for difficult-to-pair controllers
- **Bluetooth stack reset**: Automatically resets Bluetooth when needed
- **MAC address detection**: Recognizes DualShock 4 controllers by hardware signatures

### Troubleshooting Controllers
1. **Controller not found during scan**:
   - Ensure controller is in pairing mode (hold PS + Share for 3-5 seconds)
   - Controller light should flash white
   - Try resetting controller (small button on back)

2. **Controller found but won't pair**:
   - Run `./scripts/controller-manager.sh setup` to install dependencies
   - Try different pairing methods (script tries multiple approaches automatically)
   - Check Bluetooth service: `systemctl status bluetooth`

3. **Controller disconnects frequently**:
   - Check battery level
   - Ensure controller is "trusted": the pairing script handles this automatically
   - Try wired connection for debugging

### Supported Controllers
- DualShock 4 (all variants)
- Sony Interactive Entertainment Wireless Controller
- Compatible with MAC prefixes: 00:1B:DC, A0:AB:51, 00:26:43, 20:50:E7, 00:1E:3D

---

## File Structure

```
doombox/
├── README.md                    # This file
├── setup.sh                    # Main installation script
├── uninstall.sh                # Clean removal script
├── requirements.txt            # Python dependencies
├── src/                        # Core application files
│   ├── kiosk-manager.py        # Main kiosk controller
│   ├── controller-input.py     # DualShock 4 input handling
│   └── webhook.py              # API/webhook listener
├── config/                     # Configuration files
│   └── config.py               # Main configuration
├── scripts/                    # System scripts
│   ├── controller-manager.sh   # Controller management
│   └── test-suite.sh          # Comprehensive tests
├── web/                        # Web interface
│   └── index.html             # Form page
├── assets/                     # Static assets
│   ├── fonts/                 # Font files
│   ├── icons/                 # Icon library
│   └── vid/                   # Demo videos
├── logs/                       # Application logs
└── .github/                    # GitHub configuration
    └── instructions/           # Development guidelines
```

---

## Development Log

### 2025-07-06: Codebase Consolidation & Cleanup
- **Goal**: Reorganize codebase according to project instructions
- **Actions**:
  - Consolidated 8+ controller scripts into single `controller-input.py` module
  - Moved files to proper directory structure (src/, config/, scripts/, web/, assets/)
  - Removed redundant README files (merged into main README.md)
  - Created unified `controller-manager.sh` script
  - Implemented comprehensive `test-suite.sh` for validation
  - Updated file naming to follow kebab-case convention
  
- **Files Consolidated**:
  - `advanced_controller_pair.py` + `pair_controller.sh` + `debug_controller.sh` + others → `src/controller-input.py`
  - `kiosk.py` → `src/kiosk-manager.py`
  - `config.py` → `config/config.py`
  - `index.html` → `web/index.html`
  - Multiple controller scripts → `scripts/controller-manager.sh`
  - `test_advanced_controller.sh` → `scripts/test-suite.sh`

- **Files Removed** (to be cleaned up):
  - `ADVANCED_CONTROLLER_README.md`
  - `ADVANCED_CONTROLLER_SUMMARY.md`  
  - `CONTROLLER_README.md`
  - `advanced_controller_pair.py`
  - `advanced_controller_pair.sh`
  - `pair_controller.sh`
  - `debug_controller.sh`
  - `controller_overview.sh`
  - `setup_controller.sh`
  - `test_advanced_controller.sh`
  - `auto_connect_controller.sh`
  - `filetree.json`

### 2025-07-06: Advanced Controller Pairing System
- **Issue**: DualShock 4 controllers were being detected during Bluetooth scan but pairing would fail
- **Solution**: Created advanced controller pairing system with multiple pairing strategies
- **Key Features**:
  - Multiple pairing approaches (standard, connect-first, Bluetooth reset, manual auth)
  - Extended 45-second scan timeout with progress indicators
  - DualShock 4 MAC address prefix recognition
  - Automatic Bluetooth stack reset when pairing fails
  - Comprehensive diagnostics and troubleshooting tools
  - Color-coded output with verbose logging options

*Built for satan 🖤*
