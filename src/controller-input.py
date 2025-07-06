#!/usr/bin/env python3
"""
DoomBox Controller Input Handler
Consolidated DualShock 4 controller management for DoomBox kiosk
Handles pairing, connection, input processing, and Konami code detection
"""

import subprocess
import time
import sys
import os
import signal
import re
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
def setup_logging():
    """Setup logging with fallback if log directory doesn't exist"""
    try:
        log_dir = '/opt/doombox/logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/doombox/logs/controller.log'),
                logging.StreamHandler()
            ]
        )
    except (OSError, PermissionError):
        # Fallback to console-only logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )

setup_logging()
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

class ControllerState(Enum):
    """Controller connection states"""
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    PAIRING = "pairing"
    CONNECTED = "connected"
    TESTING = "testing"
    ERROR = "error"

@dataclass
class ControllerInfo:
    """Controller information structure"""
    mac: str
    name: str
    paired: bool = False
    connected: bool = False
    trusted: bool = False
    battery_level: Optional[int] = None

class KonamiCode:
    """Konami code sequence detector"""
    SEQUENCE = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
    
    def __init__(self):
        self.current_sequence = []
        self.last_input_time = 0
        self.timeout = 3.0  # Reset sequence after 3 seconds of no input
    
    def process_input(self, button: str) -> bool:
        """Process button input and check for Konami code completion"""
        current_time = time.time()
        
        # Reset sequence if too much time has passed
        if current_time - self.last_input_time > self.timeout:
            self.current_sequence = []
        
        self.last_input_time = current_time
        
        # Check if this input matches the next expected input
        if len(self.current_sequence) < len(self.SEQUENCE):
            if button.lower() == self.SEQUENCE[len(self.current_sequence)]:
                self.current_sequence.append(button.lower())
                logger.info(f"Konami code progress: {len(self.current_sequence)}/{len(self.SEQUENCE)}")
                
                # Check if sequence is complete
                if len(self.current_sequence) == len(self.SEQUENCE):
                    self.current_sequence = []  # Reset for next time
                    return True
            else:
                # Wrong input, reset sequence
                self.current_sequence = []
        
        return False

class ControllerManager:
    """Unified DualShock 4 controller management"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.state = ControllerState.DISCONNECTED
        self.controller_info: Optional[ControllerInfo] = None
        self.konami_detector = KonamiCode()
        
        # Configuration
        self.scan_timeout = 45
        self.pair_timeout = 20
        self.connect_timeout = 15
        self.max_retries = 5
        
        # DualShock 4 identifiers
        self.ds4_identifiers = [
            "Wireless Controller",
            "DUALSHOCK 4 Wireless Controller", 
            "Sony Interactive Entertainment Wireless Controller",
            "Controller",
            "DS4"
        ]
        
        # Common DualShock 4 MAC prefixes
        self.ds4_mac_prefixes = [
            "00:1B:DC",
            "A0:AB:51", 
            "00:26:43",
            "20:50:E7",
            "00:1E:3D"
        ]
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load saved controller configuration
        self._load_controller_config()
    
    def _signal_handler(self, signum, frame):
        """Handle script interruption"""
        logger.info("Controller manager interrupted")
        self._cleanup()
        sys.exit(1)
    
    def _cleanup(self):
        """Clean up resources"""
        try:
            subprocess.run(["bluetoothctl", "scan", "off"], 
                         capture_output=True, text=True, timeout=5)
        except:
            pass
    
    def _log(self, message: str, color: str = Colors.NC):
        """Log message with optional color"""
        if self.verbose:
            print(f"{color}{message}{Colors.NC}")
        logger.info(message)
    
    def _run_command(self, command: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        """Run a shell command with timeout"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            if self.verbose:
                logger.debug(f"Command: {' '.join(command)}, Result: {result.returncode}")
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(command)}")
            raise
        except Exception as e:
            logger.error(f"Command failed: {' '.join(command)}, Error: {e}")
            raise
    
    def _load_controller_config(self):
        """Load saved controller configuration"""
        config_file = "/opt/doombox/config/controller.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.controller_info = ControllerInfo(
                        mac=config.get('mac', ''),
                        name=config.get('name', ''),
                        paired=config.get('paired', False),
                        connected=config.get('connected', False),
                        trusted=config.get('trusted', False)
                    )
                    logger.info(f"Loaded controller config: {self.controller_info.mac}")
        except Exception as e:
            logger.error(f"Failed to load controller config: {e}")
    
    def _save_controller_config(self):
        """Save controller configuration"""
        if not self.controller_info:
            return
        
        config_file = "/opt/doombox/config/controller.json"
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            config = {
                'mac': self.controller_info.mac,
                'name': self.controller_info.name,
                'paired': self.controller_info.paired,
                'connected': self.controller_info.connected,
                'trusted': self.controller_info.trusted,
                'last_connected': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved controller config: {self.controller_info.mac}")
        except Exception as e:
            logger.error(f"Failed to save controller config: {e}")
    
    def check_system_dependencies(self) -> bool:
        """Check if required system dependencies are available"""
        required_commands = ["bluetoothctl", "hciconfig", "rfkill", "systemctl"]
        
        missing_deps = []
        for cmd in required_commands:
            try:
                result = subprocess.run(["which", cmd], capture_output=True, text=True)
                if result.returncode != 0:
                    missing_deps.append(cmd)
            except:
                missing_deps.append(cmd)
        
        if missing_deps:
            logger.error(f"Missing dependencies: {missing_deps}")
            return False
        
        return True
    
    def setup_bluetooth(self) -> bool:
        """Setup and prepare Bluetooth for controller pairing"""
        try:
            # Unblock Bluetooth
            self._run_command(["sudo", "rfkill", "unblock", "bluetooth"])
            
            # Start Bluetooth service
            self._run_command(["sudo", "systemctl", "start", "bluetooth"])
            
            # Power on adapter
            self._run_command(["sudo", "hciconfig", "hci0", "up"])
            
            # Configure bluetoothctl
            commands = [
                ["bluetoothctl", "power", "on"],
                ["bluetoothctl", "discoverable", "on"],
                ["bluetoothctl", "pairable", "on"],
                ["bluetoothctl", "agent", "on"],
                ["bluetoothctl", "default-agent"]
            ]
            
            for cmd in commands:
                self._run_command(cmd, timeout=5)
            
            logger.info("Bluetooth setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Bluetooth: {e}")
            return False
    
    def scan_for_controllers(self) -> List[ControllerInfo]:
        """Scan for DualShock 4 controllers"""
        self.state = ControllerState.SCANNING
        self._log(f"Scanning for controllers ({self.scan_timeout}s)...", Colors.YELLOW)
        
        found_controllers = []
        
        try:
            # Start scanning
            self._run_command(["bluetoothctl", "scan", "on"])
            
            scan_start = time.time()
            while time.time() - scan_start < self.scan_timeout:
                result = self._run_command(["bluetoothctl", "devices"], timeout=5)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if not line.strip():
                            continue
                        
                        match = re.match(r'Device\s+([0-9A-Fa-f:]{17})\s+(.+)', line)
                        if match:
                            mac_addr = match.group(1)
                            device_name = match.group(2)
                            
                            if self._is_ds4_controller(mac_addr, device_name):
                                controller = ControllerInfo(mac=mac_addr, name=device_name)
                                if controller not in found_controllers:
                                    found_controllers.append(controller)
                                    self._log(f"Found controller: {mac_addr} ({device_name})", Colors.GREEN)
                
                time.sleep(1)
            
            self._run_command(["bluetoothctl", "scan", "off"])
            
        except Exception as e:
            logger.error(f"Error during controller scan: {e}")
        
        self.state = ControllerState.DISCONNECTED
        return found_controllers
    
    def _is_ds4_controller(self, mac: str, name: str) -> bool:
        """Check if device is a DualShock 4 controller"""
        # Check name
        for identifier in self.ds4_identifiers:
            if identifier.lower() in name.lower():
                return True
        
        # Check MAC prefix
        for prefix in self.ds4_mac_prefixes:
            if mac.upper().startswith(prefix):
                return True
        
        return False
    
    def pair_controller(self, mac_address: str) -> bool:
        """Pair with a specific controller"""
        self.state = ControllerState.PAIRING
        self._log(f"Pairing with controller {mac_address}...", Colors.YELLOW)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = self._run_command(["bluetoothctl", "pair", mac_address], 
                                         timeout=self.pair_timeout)
                if result.returncode == 0:
                    self._log("Controller paired successfully", Colors.GREEN)
                    return True
                else:
                    self._log(f"Pairing attempt {attempt} failed", Colors.RED)
                    if attempt < self.max_retries:
                        time.sleep(3)
                        
            except Exception as e:
                logger.error(f"Pairing attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(3)
        
        self.state = ControllerState.ERROR
        return False
    
    def connect_controller(self, mac_address: str) -> bool:
        """Connect to a paired controller"""
        self._log(f"Connecting to controller {mac_address}...", Colors.YELLOW)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = self._run_command(["bluetoothctl", "connect", mac_address], 
                                         timeout=self.connect_timeout)
                if result.returncode == 0:
                    self._log("Controller connected successfully", Colors.GREEN)
                    self.state = ControllerState.CONNECTED
                    return True
                else:
                    self._log(f"Connection attempt {attempt} failed", Colors.RED)
                    if attempt < self.max_retries:
                        time.sleep(2)
                        
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(2)
        
        self.state = ControllerState.ERROR
        return False
    
    def auto_connect(self) -> bool:
        """Automatically connect to saved controller"""
        if not self.controller_info or not self.controller_info.mac:
            logger.warning("No saved controller configuration found")
            return False
        
        logger.info(f"Attempting auto-connect to {self.controller_info.mac}")
        
        # Try to connect to saved controller
        if self.connect_controller(self.controller_info.mac):
            self.controller_info.connected = True
            self._save_controller_config()
            return True
        
        return False
    
    def test_controller_input(self, duration: int = 5) -> bool:
        """Test controller input for specified duration"""
        self.state = ControllerState.TESTING
        self._log(f"Testing controller input for {duration} seconds...", Colors.CYAN)
        
        try:
            # Check for joystick device
            result = subprocess.run(["ls", "/dev/input/js*"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("No joystick device found")
                return False
            
            js_devices = result.stdout.strip().split('\n')
            logger.info(f"Found joystick device: {js_devices[0]}")
            
            # Test input using jstest
            test_result = subprocess.run(["timeout", str(duration), "jstest", "--event", js_devices[0]], 
                                       capture_output=True, text=True)
            
            if test_result.returncode in [0, 124]:  # 124 is timeout exit code
                self._log("Controller input test completed", Colors.GREEN)
                self.state = ControllerState.CONNECTED
                return True
            else:
                logger.error("Controller input test failed")
                return False
                
        except Exception as e:
            logger.error(f"Controller input test failed: {e}")
            return False
    
    def get_controller_status(self) -> Dict[str, Any]:
        """Get current controller status"""
        status = {
            'state': self.state.value,
            'controller_info': None,
            'bluetooth_service': False,
            'bluetooth_adapter': False,
            'joystick_devices': []
        }
        
        # Check Bluetooth service
        try:
            result = self._run_command(["systemctl", "is-active", "bluetooth"])
            status['bluetooth_service'] = result.returncode == 0
        except:
            pass
        
        # Check Bluetooth adapter
        try:
            result = self._run_command(["hciconfig", "hci0"])
            status['bluetooth_adapter'] = result.returncode == 0
        except:
            pass
        
        # Check joystick devices
        try:
            result = subprocess.run(["ls", "/dev/input/js*"], capture_output=True, text=True)
            if result.returncode == 0:
                status['joystick_devices'] = result.stdout.strip().split('\n')
        except:
            pass
        
        # Add controller info if available
        if self.controller_info:
            status['controller_info'] = {
                'mac': self.controller_info.mac,
                'name': self.controller_info.name,
                'paired': self.controller_info.paired,
                'connected': self.controller_info.connected,
                'trusted': self.controller_info.trusted
            }
        
        return status
    
    def start_input_monitoring(self, callback=None):
        """Start monitoring controller input (for game integration)"""
        if not self.controller_info or not self.controller_info.connected:
            logger.error("No controller connected for input monitoring")
            return False
        
        logger.info("Starting controller input monitoring...")
        
        # This would be implemented with appropriate input library
        # For now, just a placeholder
        try:
            # Monitor input events and call callback
            # Implementation would depend on the chosen input library
            pass
        except Exception as e:
            logger.error(f"Input monitoring failed: {e}")
            return False
        
        return True

def main():
    """Main function for standalone controller management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DoomBox Controller Management')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--scan', action='store_true', help='Scan for controllers')
    parser.add_argument('--pair', type=str, help='Pair with specific MAC address')
    parser.add_argument('--connect', type=str, help='Connect to specific MAC address')
    parser.add_argument('--auto-connect', action='store_true', help='Auto-connect to saved controller')
    parser.add_argument('--status', action='store_true', help='Show controller status')
    parser.add_argument('--test', action='store_true', help='Test controller input')
    
    args = parser.parse_args()
    
    # Create controller manager
    manager = ControllerManager(verbose=args.verbose)
    
    try:
        if args.scan:
            if manager.setup_bluetooth():
                controllers = manager.scan_for_controllers()
                if controllers:
                    print(f"Found {len(controllers)} controller(s):")
                    for ctrl in controllers:
                        print(f"  • {ctrl.mac} ({ctrl.name})")
                else:
                    print("No controllers found")
            
        elif args.pair:
            if manager.setup_bluetooth():
                if manager.pair_controller(args.pair):
                    print("Controller paired successfully")
                else:
                    print("Failed to pair controller")
        
        elif args.connect:
            if manager.connect_controller(args.connect):
                print("Controller connected successfully")
            else:
                print("Failed to connect controller")
        
        elif args.auto_connect:
            if manager.auto_connect():
                print("Auto-connect successful")
            else:
                print("Auto-connect failed")
        
        elif args.status:
            status = manager.get_controller_status()
            print(json.dumps(status, indent=2))
        
        elif args.test:
            if manager.test_controller_input():
                print("Controller test completed")
            else:
                print("Controller test failed")
        
        else:
            print("No action specified. Use --help for options.")
    
    except KeyboardInterrupt:
        print("\nController management interrupted")
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        manager._cleanup()

if __name__ == "__main__":
    main()
