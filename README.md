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
/opt/doombox/pair_controller.sh
```

### 6. Configure Your Web Form URL

Edit the QR code URL in `/opt/doombox/kiosk.py`:
```python
self.form_url = "https://your-username.github.io/doombox-form/"
```

Or update the configuration in `/opt/doombox/config.py`:
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

## File Structure

```
/opt/doombox/
├── kiosk.py              # Main application (copied from repo)
├── config.py             # Configuration file (copied from repo)
├── webhook.py            # Webhook bridge (copied from repo)
├── venv/                 # Python virtual environment
├── doom/
│   └── DOOM.WAD         # Game data (downloaded)
├── form/                 # Web form files (copied from repo)
│   ├── index.html
│   └── CNAME
├── logs/                # Application logs
├── scores.db            # SQLite score database
├── start.sh             # Startup script
├── start_x_display.sh   # X11 startup helper
├── test_doom.sh         # Test DOOM directly
├── test_kiosk.sh        # Test kiosk application
└── pair_controller.sh   # Controller pairing helper
```

## Configuration

### Display Settings
- **Kiosk Resolution**: 1280x960
- **DOOM Resolution**: 640x480 (scaled up)
- **Fullscreen Mode**: Enabled by default

### Database Schema
```sql
CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    score INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    level_reached INTEGER DEFAULT 1,
    time_played INTEGER DEFAULT 0
);
```

## Usage

### Normal Operation
1. System boots and displays QR code + leaderboard
2. Users scan QR code and fill out web form
3. Form submission triggers game start via MQTT/webhook
4. Player plays DOOM, score is automatically recorded
5. Updated leaderboard displays after game ends

### Test Mode
- Use Konami code on controller: `↑↑↓↓←→←→BA`
- Or run: `/opt/doombox/test_doom.sh`
- Test games don't affect the leaderboard

### Manual Control
```bash
# Start kiosk manually
sudo /opt/doombox/test_kiosk.sh

# Check service status
sudo systemctl status doombox

# View logs
sudo journalctl -u doombox -f

# Restart service
sudo systemctl restart doombox

# View scores
/opt/doombox/view_scores.sh
```

## XFCE Desktop Integration

After setup, you'll find a "DoomBox" category in the XFCE Applications Menu with these tools:

- **DoomBox Kiosk** - Main kiosk application
- **Test DOOM (Wrapper)** - Test DOOM via lzdoom wrapper
- **Test dsda-doom (Direct)** - Test dsda-doom directly
- **Debug Controller** - Test controller input
- **Pair Controller** - Bluetooth pairing helper
- **View High Scores** - Database viewer
- **Start/Stop Kiosk Service** - Service management
- **Start X Display** - X11 startup helper

## Web Form Integration

### GitHub Pages Setup
1. The `index.html` file is copied to `/opt/doombox/form/`
2. Deploy this to GitHub Pages
3. Update the QR code URL in the kiosk configuration
4. Form submissions trigger the kiosk via MQTT or webhook

### MQTT Integration
The kiosk listens on `doombox/start_game` topic:
```json
{
  "player_name": "PlayerName"
}
```

### Webhook Integration
Create a file at `/opt/doombox/new_player.json`:
```json
{
  "player_name": "PlayerName"
}
```

## Troubleshooting

### Setup Issues
```bash
# Check if all files were copied properly
ls -la /opt/doombox/
# Should show kiosk.py, config.py, etc.

# Verify X11 is running
export DISPLAY=:0
xset q

# Check services
systemctl status bluetooth
systemctl status mosquitto
systemctl status doombox
```

### Controller Issues
```bash
# Check if controller is detected
ls /dev/input/js*

# Test controller input
jstest /dev/input/js0

# Debug controller
/opt/doombox/debug_controller.sh

# Bluetooth status
sudo systemctl status bluetooth
```

### DOOM Issues
```bash
# Test dsda-doom directly
cd /opt/doombox/doom
dsda-doom -iwad DOOM.WAD

# Test wrapper
/usr/local/bin/lzdoom -iwad /opt/doombox/doom/DOOM.WAD

# Check installation
which dsda-doom
```

### Display Issues
```bash
# Check current resolution
xrandr

# Start X server manually
/opt/doombox/start_x_display.sh

# Test different resolution
xrandr --output HDMI-1 --mode 1280x960
```

## Auto-Boot Kiosk Mode

For production deployment:

```bash
# Set to boot to console (no desktop)
sudo systemctl set-default multi-user.target

# Enable auto-start of kiosk
sudo systemctl enable doombox.service

# Reboot to test
sudo reboot
```

## Development

### Repository Structure
```
doombox/
├── kiosk.py              # Main kiosk application
├── config.py             # Configuration settings
├── webhook.py            # Webhook bridge server
├── setup.sh              # Installation script
├── index.html            # Web registration form
├── CNAME                 # GitHub Pages domain
├── README.md             # This file
├── lmao.gif              # Floating animation
└── formsubmit.jpg        # Form submission image
```

### Making Changes
1. Edit files in the repository
2. Copy changes to `/opt/doombox/` or re-run setup
3. Restart the kiosk service

## Security Notes

⚠️ **This setup runs as root for simplicity**

For production use, consider:
- Creating a dedicated user account
- Implementing proper file permissions
- Using systemd user services
- Sandboxing the DOOM process

## Customization

### Changing Colors/Theme
Edit the color constants in `config.py` or `kiosk.py`:
```python
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    # ... etc
}
```

### Adding Custom DOOM Mods
1. Place mod files in `/opt/doombox/doom/`
2. Update the DOOM command in `config.py`
3. Add `-file modname.wad` parameter

### Customizing Score Display
Modify the `draw_screen()` method in `kiosk.py` to change:
- Number of scores shown
- Score formatting
- Display layout

## License

MIT License - see LICENSE file for details

## Credits

- **Hardware**: Radxa Zero
- **Game**: DOOM (id Software)
- **Engine**: dsda-doom
- **Inspired by**: Classic arcade cabinets

---

*Built for satan 🖤*
