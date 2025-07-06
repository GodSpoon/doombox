# DoomBox Controller Scripts

This directory contains scripts for managing DualShock 4 controllers with the DoomBox system.

## Scripts

### `pair_controller.sh`
**Main controller pairing script**
- Pairs a DualShock 4 controller via Bluetooth
- Handles the complete pairing process
- Includes troubleshooting and testing
- Saves configuration for future use

**Usage:**
```bash
# Standard pairing
./pair_controller.sh

# Scan for controllers only
./pair_controller.sh --scan-only

# Force re-pair existing controller
./pair_controller.sh --force

# Pair specific MAC address
./pair_controller.sh --mac 12:34:56:78:90:AB

# Show help
./pair_controller.sh --help
```

### `debug_controller.sh`
**Controller debugging and testing script**
- Comprehensive system status check
- Tests controller input functionality
- Provides detailed troubleshooting information
- Continuous monitoring mode

**Usage:**
```bash
# Full debug report
./debug_controller.sh

# Quick status check
./debug_controller.sh --status

# Test controller input
./debug_controller.sh --test-input

# Test with pygame
./debug_controller.sh --pygame-test

# Continuous monitoring
./debug_controller.sh --continuous
```

### `auto_connect_controller.sh`
**Automatic controller connection script**
- Automatically connects to paired controllers
- Designed for systemd services or startup scripts
- Logs connection attempts and status

**Usage:**
```bash
# Auto-connect to paired controller
./auto_connect_controller.sh
```

## Setup Process

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y bluetooth bluez bluez-tools joystick jstest-gtk
```

### 2. Pair Your Controller
```bash
./pair_controller.sh
```

Follow the on-screen instructions:
1. Turn OFF your DualShock 4 controller
2. Hold PS + Share buttons for 3-5 seconds
3. Controller light should flash white (pairing mode)
4. Press Enter to continue with pairing

### 3. Test Controller
```bash
./debug_controller.sh --test-input
```

### 4. Verify Setup
```bash
./debug_controller.sh --status
```

## Troubleshooting

### Controller Not Found
- Make sure controller is in pairing mode (flashing white light)
- Reset controller using small button on back
- Check Bluetooth service: `systemctl status bluetooth`
- Try: `sudo systemctl restart bluetooth`

### Pairing Fails
- Controller may be paired to another device
- Use `./pair_controller.sh --force` to re-pair
- Check if controller is compatible (DualShock 4 v1/v2)

### No Joystick Device
- Controller paired but no `/dev/input/js*` device
- Check with `./debug_controller.sh`
- May need to install additional drivers

### Connection Issues
- Use `./debug_controller.sh --continuous` to monitor
- Check Bluetooth signal strength
- Ensure controller is charged

## Files Created

### `~/.doombox_controller`
Configuration file containing:
- Controller MAC address
- Controller name
- Pairing date

### `/var/log/doombox_controller.log`
Auto-connect log file (if using auto-connect script)

## Integration with DoomBox

The controller scripts are designed to work with the main DoomBox application:

1. **Konami Code Detection**: The main kiosk application can detect the Konami code sequence
2. **Game Control**: Controller works with DOOM and other games
3. **Auto-reconnect**: Controller automatically reconnects on system boot

## systemd Integration

To automatically connect controllers on boot, create a systemd service:

```bash
sudo tee /etc/systemd/system/doombox-controller.service << 'EOF'
[Unit]
Description=DoomBox Controller Auto-Connect
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=oneshot
ExecStart=/opt/doombox/auto_connect_controller.sh
RemainAfterExit=yes
User=doombox
Group=doombox

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable doombox-controller.service
sudo systemctl start doombox-controller.service
```

## Supported Controllers

- **DualShock 4 (PS4)**: Primary target, fully supported
- **DualShock 4 v2**: Should work identically
- **Other controllers**: May work but not tested

## Technical Details

### Bluetooth Pairing Process
1. Enable Bluetooth adapter
2. Scan for devices
3. Pair with discovered controller
4. Trust the device
5. Connect to device
6. Test functionality

### Expected Device Names
- `Sony Interactive Entertainment Wireless Controller`
- `Wireless Controller`
- `DUALSHOCK 4 Wireless Controller`

### Common MAC Prefixes
- `00:1B:DC:xx:xx:xx` (Common DS4 prefix)
- `A0:AB:51:xx:xx:xx` (Alternative prefix)

## Logging

All scripts provide detailed logging:
- **Success/Error messages**: Color-coded output
- **Verbose mode**: Available with `-v` flag
- **Log files**: Auto-connect script logs to `/var/log/doombox_controller.log`

## Security Notes

- Scripts can run as regular user (no root required for most operations)
- Bluetooth service management may require sudo
- Configuration files stored in user home directory

## Version History

- **v1.0.0**: Initial release with pairing, debugging, and auto-connect functionality
