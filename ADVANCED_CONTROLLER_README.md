# Advanced Controller Pairing for DoomBox

This advanced controller pairing system addresses common issues with DualShock 4 Bluetooth pairing and provides better diagnostics and troubleshooting.

## Files

- `advanced_controller_pair.py` - Main Python-based pairing script
- `advanced_controller_pair.sh` - Shell wrapper with additional utilities

## Features

### Enhanced Pairing Process
- **Multiple pairing methods**: Tries different approaches if standard pairing fails
- **Bluetooth stack reset**: Automatically resets Bluetooth when needed
- **Better error handling**: More detailed error messages and recovery attempts
- **Comprehensive scanning**: Longer scan times and better device detection
- **MAC address detection**: Recognizes DualShock 4 controllers by MAC prefixes

### Troubleshooting Tools
- **System diagnostics**: Check Bluetooth hardware, services, and dependencies
- **Status monitoring**: Show current controller and Bluetooth status
- **Bluetooth reset**: Reset Bluetooth stack to clear stuck states
- **Dependency installation**: Automatically install required packages

### Improved User Experience
- **Color-coded output**: Clear visual feedback for different message types
- **Interactive prompts**: Step-by-step guidance through pairing process
- **Verbose mode**: Detailed logging for debugging
- **Progress indicators**: Show scan progress and retry attempts

## Usage

### Quick Start
```bash
# Interactive pairing (recommended)
./advanced_controller_pair.sh

# Or use Python script directly
./advanced_controller_pair.py
```

### Common Commands
```bash
# Check current status
./advanced_controller_pair.sh --status

# Run troubleshooting diagnostics
./advanced_controller_pair.sh --troubleshoot

# Force re-pair existing controller
./advanced_controller_pair.sh --force

# Scan for controllers only
./advanced_controller_pair.sh --scan-only

# Reset Bluetooth stack
./advanced_controller_pair.sh --reset-bluetooth

# Install dependencies
./advanced_controller_pair.sh --install-deps
```

### Advanced Options
```bash
# Pair specific MAC address
./advanced_controller_pair.sh --mac 20:50:E7:D2:6F:E3

# Enable verbose output
./advanced_controller_pair.sh --verbose

# Show help
./advanced_controller_pair.sh --help
```

## How It Works

### Pairing Process
1. **System Check**: Verify dependencies, Bluetooth service, and hardware
2. **Bluetooth Preparation**: Configure adapter for pairing mode
3. **Controller Scan**: Extended scan with multiple device identifiers
4. **Multiple Pairing Attempts**: Try different pairing methods:
   - Standard bluetoothctl pairing
   - Connect-first pairing
   - Bluetooth stack reset and retry
   - Manual authorization
5. **Trust and Connect**: Trust device and establish connection
6. **Testing**: Verify joystick device creation and input
7. **Configuration**: Save controller info for auto-connection

### Issue Resolution

The script addresses common DualShock 4 pairing problems:

#### Controller Not Found
- **Extended scan time**: 45 seconds vs 30 seconds
- **Multiple identifiers**: Recognizes various DS4 device names
- **MAC prefix detection**: Identifies controllers by MAC address patterns
- **Bluetooth reset**: Clears stuck scanning states

#### Pairing Failures
- **Multiple retry attempts**: Up to 5 attempts with different methods
- **Connect-first approach**: Some controllers prefer connection before pairing
- **Bluetooth stack reset**: Clears authentication cache and restarts services
- **Manual authorization**: Handles controllers requiring user confirmation

#### Connection Issues
- **Trust establishment**: Ensures controller is trusted for auto-connection
- **Connection verification**: Confirms successful connection before proceeding
- **Input device testing**: Verifies joystick device creation and functionality

## Troubleshooting

### Common Issues

#### "No Bluetooth adapter found"
```bash
# Check hardware
./advanced_controller_pair.sh --troubleshoot

# Try unblocking Bluetooth
sudo rfkill unblock bluetooth

# Reset Bluetooth
./advanced_controller_pair.sh --reset-bluetooth
```

#### "Controller not found during scan"
1. Ensure controller is in pairing mode (flashing white light)
2. Hold PS + Share buttons for 3-5 seconds
3. Reset controller using small button on back
4. Try scanning longer: `./advanced_controller_pair.sh --verbose`

#### "Pairing fails but controller is detected"
```bash
# Force unpair and retry
./advanced_controller_pair.sh --force

# Reset Bluetooth stack
./advanced_controller_pair.sh --reset-bluetooth

# Check if paired to another device first
```

#### "No joystick device created"
```bash
# Install joystick packages
sudo apt install joystick jstest-gtk

# Check input devices
ls -l /dev/input/js*

# Test controller
jstest /dev/input/js0
```

### Diagnostic Information

The troubleshooting tool checks:
- System dependencies (bluetoothctl, hciconfig, rfkill)
- Bluetooth hardware status
- Service status (bluetooth daemon)
- Paired and connected devices
- Joystick devices
- Configuration files

### Log Files

- Controller configuration: `~/.doombox_controller`
- Bluetooth logs: `journalctl -u bluetooth`
- System logs: `dmesg | grep -i bluetooth`

## Technical Details

### Supported Controllers
- DualShock 4 (original and v2)
- Sony Interactive Entertainment Wireless Controller
- Generic wireless controllers with compatible protocols

### MAC Address Prefixes
The script recognizes these common DualShock 4 MAC prefixes:
- `00:1B:DC` (most common)
- `A0:AB:51` 
- `00:26:43`
- `20:50:E7`
- `00:1E:3D`

### Dependencies
- Python 3
- bluetoothctl (bluez package)
- hciconfig (bluez-tools)
- rfkill
- systemctl
- jstest (joystick package) - optional for testing

### Configuration
Controller information is saved to `~/.doombox_controller`:
```
CONTROLLER_MAC=20:50:E7:D2:6F:E3
CONTROLLER_NAME=Wireless Controller
PAIRED_DATE=2025-01-20 15:30:45
```

## Integration with DoomBox

The advanced pairing script integrates with existing DoomBox controller functionality:

- **Configuration compatibility**: Uses same config file format as existing scripts
- **Auto-connection**: Works with `auto_connect_controller.sh`
- **Debugging**: Compatible with `debug_controller.sh`
- **Kiosk integration**: Controllers work immediately with main DoomBox interface

## Comparison with Original Script

| Feature | Original Script | Advanced Script |
|---------|----------------|-----------------|
| Pairing methods | 1 | 4 different approaches |
| Scan timeout | 30 seconds | 45 seconds |
| MAC detection | Generic | DS4-specific prefixes |
| Error handling | Basic | Comprehensive |
| Bluetooth reset | Manual | Automatic |
| Diagnostics | Limited | Extensive |
| Progress feedback | Minimal | Detailed |
| Troubleshooting | Basic tips | Interactive diagnostics |

## Future Enhancements

Potential improvements:
- Support for other controller types (Xbox, 8BitDo, etc.)
- GUI interface for easier use
- Automatic controller firmware updates
- Battery level monitoring
- Multiple controller support
- Configuration profiles for different users

## License

This script is part of the DoomBox project and follows the same licensing terms.
