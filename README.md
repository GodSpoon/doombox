# shmegl's DoomBox

**Highest score gets a free tattoo**

An interactive gaming kiosk built on Radxa Zero that displays a QR code for user registration, launches DOOM with custom player names, tracks high scores, and awards prizes to top players.

## Hardware Requirements

- Radxa Zero SBC (4GB RAM recommended)
- 2048x1536 display (running at 1280x960)
- DualShock 4 controller (Bluetooth or wired)
- Network connectivity (WiFi/Ethernet)

## Software Stack

- **OS**: Dietpi
- **Desktop**: XFCE4
- **Game Engine**: LZDoom
- **Backend**: Python 3 with Flask
- **Database**: SQLite
- **Communication**: MQTT (optional)

## Quick Setup

1. **Clone the repository on your Radxa Zero:**
   ```bash
   git clone https://github.com/your-username/doombox.git
   cd doombox
   ```

2. **Run the setup script as root:**
   ```bash
   sudo bash setup.sh
   ```

3. **Pair your DualShock 4 controller:**
   ```bash
   /opt/doombox/pair_controller.sh
   ```

4. **Update the QR code URL** in `/opt/doombox/kiosk.py` to point to your GitHub Pages form

5. **Reboot to start the kiosk automatically**

## Features

### 🎮 Game Integration
- Launches LZDoom with custom player names & overlay
- Automatic game exit detection and score logging

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
├── kiosk.py              # Main application
├── venv/                 # Python virtual environment
├── doom/
│   └── DOOM.WAD         # Game data
├── logs/                # Application logs
├── scores.db            # SQLite score database
├── start.sh             # Startup script
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
    level_reached INTEGER DEFAULT 1
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
```

## Web Form Integration

### GitHub Pages Setup
1. Create a new repository for your form
2. Enable GitHub Pages in repository settings
3. Use the provided HTML template in `form/index.html`
4. Update the form action URL to trigger your kiosk

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

### Controller Issues
```bash
# Check if controller is detected
ls /dev/input/js*

# Test controller input
jstest /dev/input/js0

# Bluetooth status
sudo systemctl status bluetooth
```

### DOOM Issues
```bash
# Test DOOM directly
cd /opt/doombox/doom
lzdoom -iwad DOOM.WAD

# Check DOOM installation
which lzdoom
```

### Display Issues
```bash
# Check current resolution
xrandr

# Test different resolution
xrandr --output HDMI-1 --mode 1280x960
```

## Customization

### Changing Colors/Theme
Edit the color constants in `kiosk.py`:
```python
self.BLACK = (0, 0, 0)
self.WHITE = (255, 255, 255)
self.RED = (255, 0, 0)
# ... etc
```

### Adding Custom DOOM Mods
1. Place mod files in `/opt/doombox/doom/`
2. Update the DOOM command in `_run_doom()` method
3. Add `-file modname.wad` parameter

### Customizing Score Display
Modify the `draw_screen()` method to change:
- Number of scores shown
- Score formatting
- Display layout

## Security Notes

⚠️ **This setup runs as root because im lazy**

For production use, consider:
- Creating a dedicated user account
- Implementing proper file permissions
- Using systemd user services
- Sandboxing the DOOM process
  
## License

MIT License - see LICENSE file for details

## Credits

- **Hardware**: Radxa Zero
- **Game**: DOOM (duh)
- **Engine**: LZDoom

---

*Built for satan 🖤*
