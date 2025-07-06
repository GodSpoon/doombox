#!/usr/bin/env python3
"""
DoomBox Advanced Controller Pairing Script
An improved Python-based script for pairing DualShock 4 controllers
Addresses common pairing issues and provides better error handling
"""

import subprocess
import time
import sys
import os
import signal
import re
import argparse
from typing import Optional, List, Dict, Any

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

class ControllerPairing:
    """Advanced DualShock 4 Controller Pairing Manager"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.controller_mac = None
        self.controller_name = None
        self.bluetooth_process = None
        self.scan_timeout = 45  # Increased timeout
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
    
    def _signal_handler(self, signum, frame):
        """Handle script interruption"""
        print(f"\n{Colors.YELLOW}Script interrupted{Colors.NC}")
        self._cleanup()
        sys.exit(1)
    
    def _cleanup(self):
        """Clean up resources"""
        if self.bluetooth_process:
            try:
                self.bluetooth_process.terminate()
                self.bluetooth_process.wait(timeout=5)
            except:
                pass
        
        # Stop scanning
        try:
            subprocess.run(["bluetoothctl", "scan", "off"], 
                         capture_output=True, text=True, timeout=5)
        except:
            pass
    
    def _log(self, message: str, color: str = Colors.NC):
        """Log message with optional color"""
        print(f"{color}{message}{Colors.NC}")
    
    def _verbose_log(self, message: str):
        """Log verbose message"""
        if self.verbose:
            self._log(f"[VERBOSE] {message}", Colors.CYAN)
    
    def _run_command(self, command: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        """Run a shell command with timeout"""
        self._verbose_log(f"Running command: {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            self._verbose_log(f"Command result: {result.returncode}, stdout: {result.stdout[:100]}...")
            return result
        except subprocess.TimeoutExpired:
            self._log(f"Command timed out: {' '.join(command)}", Colors.RED)
            raise
        except Exception as e:
            self._log(f"Command failed: {' '.join(command)}, Error: {e}", Colors.RED)
            raise
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        self._log("Checking dependencies...", Colors.YELLOW)
        
        required_commands = [
            "bluetoothctl",
            "hciconfig", 
            "rfkill",
            "systemctl"
        ]
        
        missing_deps = []
        for cmd in required_commands:
            try:
                result = subprocess.run(["which", cmd], capture_output=True, text=True)
                if result.returncode != 0:
                    missing_deps.append(cmd)
            except:
                missing_deps.append(cmd)
        
        if missing_deps:
            self._log("❌ Missing dependencies:", Colors.RED)
            for dep in missing_deps:
                self._log(f"   • {dep}", Colors.RED)
            self._log("\nInstall missing dependencies with:", Colors.YELLOW)
            self._log("   sudo apt update", Colors.CYAN)
            self._log("   sudo apt install -y bluetooth bluez bluez-tools rfkill", Colors.CYAN)
            return False
        
        self._log("✓ All dependencies found", Colors.GREEN)
        return True
    
    def check_bluetooth_hardware(self) -> bool:
        """Check if Bluetooth hardware is available and enabled"""
        self._log("Checking Bluetooth hardware...", Colors.YELLOW)
        
        # Check if Bluetooth is blocked by rfkill
        try:
            result = self._run_command(["rfkill", "list", "bluetooth"])
            if "Soft blocked: yes" in result.stdout:
                self._log("Bluetooth is soft-blocked, attempting to unblock...", Colors.YELLOW)
                unblock_result = self._run_command(["sudo", "rfkill", "unblock", "bluetooth"])
                if unblock_result.returncode != 0:
                    self._log("❌ Failed to unblock Bluetooth", Colors.RED)
                    return False
                self._log("✓ Bluetooth unblocked", Colors.GREEN)
        except:
            self._log("⚠️  Could not check rfkill status", Colors.YELLOW)
        
        # Check hciconfig
        try:
            result = self._run_command(["hciconfig", "-a"])
            if result.returncode != 0 or "hci0" not in result.stdout:
                self._log("❌ No Bluetooth adapter found", Colors.RED)
                return False
        except:
            self._log("❌ Could not check Bluetooth adapter", Colors.RED)
            return False
        
        # Power on the adapter
        try:
            self._run_command(["sudo", "hciconfig", "hci0", "up"])
            self._log("✓ Bluetooth adapter powered on", Colors.GREEN)
        except:
            self._log("❌ Failed to power on Bluetooth adapter", Colors.RED)
            return False
        
        return True
    
    def check_bluetooth_service(self) -> bool:
        """Check and start Bluetooth service if needed"""
        self._log("Checking Bluetooth service...", Colors.YELLOW)
        
        # Check if service is active
        try:
            result = self._run_command(["systemctl", "is-active", "bluetooth"])
            if result.returncode != 0:
                self._log("Starting Bluetooth service...", Colors.YELLOW)
                start_result = self._run_command(["sudo", "systemctl", "start", "bluetooth"])
                if start_result.returncode != 0:
                    self._log("❌ Failed to start Bluetooth service", Colors.RED)
                    return False
                self._log("✓ Bluetooth service started", Colors.GREEN)
            else:
                self._log("✓ Bluetooth service is running", Colors.GREEN)
        except:
            self._log("❌ Could not check Bluetooth service", Colors.RED)
            return False
        
        # Enable service for auto-start
        try:
            self._run_command(["sudo", "systemctl", "enable", "bluetooth"])
        except:
            pass  # Non-critical
        
        return True
    
    def reset_bluetooth_stack(self) -> bool:
        """Reset Bluetooth stack to clear any stuck states"""
        self._log("Resetting Bluetooth stack...", Colors.YELLOW)
        
        try:
            # Stop bluetooth service
            self._run_command(["sudo", "systemctl", "stop", "bluetooth"])
            time.sleep(2)
            
            # Reset HCI interface
            self._run_command(["sudo", "hciconfig", "hci0", "down"])
            time.sleep(1)
            self._run_command(["sudo", "hciconfig", "hci0", "up"])
            time.sleep(1)
            
            # Start bluetooth service
            self._run_command(["sudo", "systemctl", "start", "bluetooth"])
            time.sleep(3)
            
            self._log("✓ Bluetooth stack reset", Colors.GREEN)
            return True
        except:
            self._log("❌ Failed to reset Bluetooth stack", Colors.RED)
            return False
    
    def prepare_for_pairing(self) -> bool:
        """Prepare Bluetooth adapter for pairing"""
        self._log("Preparing for pairing...", Colors.YELLOW)
        
        try:
            # Make adapter discoverable and pairable
            commands = [
                ["bluetoothctl", "power", "on"],
                ["bluetoothctl", "discoverable", "on"],
                ["bluetoothctl", "pairable", "on"],
                ["bluetoothctl", "agent", "on"],
                ["bluetoothctl", "default-agent"]
            ]
            
            for cmd in commands:
                result = self._run_command(cmd, timeout=5)
                if result.returncode != 0:
                    self._log(f"Warning: Command failed: {' '.join(cmd)}", Colors.YELLOW)
                    # Continue anyway, some commands might fail but still work
            
            self._log("✓ Bluetooth adapter prepared for pairing", Colors.GREEN)
            return True
        except:
            self._log("❌ Failed to prepare Bluetooth adapter", Colors.RED)
            return False
    
    def show_pairing_instructions(self):
        """Display controller pairing instructions"""
        self._log("=" * 60, Colors.BLUE)
        self._log("  DualShock 4 Pairing Instructions", Colors.BLUE)
        self._log("=" * 60, Colors.BLUE)
        print()
        self._log("1. Turn OFF your DualShock 4 controller completely", Colors.CYAN)
        self._log("   (Hold PS button for 10 seconds if needed)", Colors.WHITE)
        print()
        self._log("2. Enter pairing mode by holding:", Colors.CYAN)
        self._log("   PS button + Share button", Colors.YELLOW)
        self._log("   for about 3-5 seconds simultaneously", Colors.WHITE)
        print()
        self._log("3. The controller light bar should start flashing WHITE", Colors.CYAN)
        self._log("   (This indicates pairing mode)", Colors.WHITE)
        print()
        self._log("4. Keep the controller close to your device", Colors.CYAN)
        self._log("   (within 1-2 meters)", Colors.WHITE)
        print()
        self._log("5. If pairing fails, try:", Colors.CYAN)
        self._log("   • Reset controller (small button on back)", Colors.WHITE)
        self._log("   • Disconnect from other devices first", Colors.WHITE)
        self._log("   • Try different USB cable for initial connection", Colors.WHITE)
        print()
        
        input(f"{Colors.GREEN}Press Enter when your controller is flashing white...{Colors.NC}")
    
    def scan_for_controllers(self) -> List[Dict[str, str]]:
        """Scan for DualShock 4 controllers"""
        self._log(f"Scanning for DualShock 4 controllers ({self.scan_timeout}s timeout)...", Colors.YELLOW)
        
        found_controllers = []
        
        try:
            # Clear previous scan results
            self._run_command(["bluetoothctl", "scan", "off"])
            time.sleep(1)
            
            # Start scanning
            self._run_command(["bluetoothctl", "scan", "on"])
            
            scan_start = time.time()
            last_update = scan_start
            
            while time.time() - scan_start < self.scan_timeout:
                # Check for discovered devices
                result = self._run_command(["bluetoothctl", "devices"], timeout=5)
                
                if result.returncode == 0:
                    devices = result.stdout.strip().split('\n')
                    current_controllers = []
                    
                    for device_line in devices:
                        if not device_line.strip():
                            continue
                        
                        # Parse device line: "Device AA:BB:CC:DD:EE:FF Device Name"
                        match = re.match(r'Device\s+([0-9A-Fa-f:]{17})\s+(.+)', device_line)
                        if match:
                            mac_addr = match.group(1)
                            device_name = match.group(2)
                            
                            # Check if this looks like a DualShock 4
                            is_ds4 = False
                            for identifier in self.ds4_identifiers:
                                if identifier.lower() in device_name.lower():
                                    is_ds4 = True
                                    break
                            
                            # Also check MAC prefix
                            if not is_ds4:
                                for prefix in self.ds4_mac_prefixes:
                                    if mac_addr.upper().startswith(prefix):
                                        is_ds4 = True
                                        break
                            
                            if is_ds4:
                                controller_info = {
                                    'mac': mac_addr,
                                    'name': device_name
                                }
                                
                                # Check if this is a new controller
                                if controller_info not in current_controllers:
                                    current_controllers.append(controller_info)
                                    
                                    # Check if we haven't seen this controller before
                                    if controller_info not in found_controllers:
                                        found_controllers.append(controller_info)
                                        self._log(f"✓ Found controller: {mac_addr} ({device_name})", Colors.GREEN)
                
                # Show progress every 5 seconds
                if time.time() - last_update >= 5:
                    remaining = int(self.scan_timeout - (time.time() - scan_start))
                    self._log(f"Scanning... {remaining}s remaining", Colors.CYAN)
                    last_update = time.time()
                
                time.sleep(1)
            
            # Stop scanning
            self._run_command(["bluetoothctl", "scan", "off"])
            
        except Exception as e:
            self._log(f"Error during scanning: {e}", Colors.RED)
            try:
                self._run_command(["bluetoothctl", "scan", "off"])
            except:
                pass
        
        if found_controllers:
            self._log(f"✓ Found {len(found_controllers)} DualShock 4 controller(s)", Colors.GREEN)
        else:
            self._log("❌ No DualShock 4 controllers found", Colors.RED)
            self._log("Troubleshooting:", Colors.YELLOW)
            self._log("   • Make sure controller is in pairing mode (flashing white)", Colors.WHITE)
            self._log("   • Try resetting controller (small button on back)", Colors.WHITE)
            self._log("   • Move controller closer to device", Colors.WHITE)
            self._log("   • Ensure controller isn't paired to another device", Colors.WHITE)
        
        return found_controllers
    
    def remove_existing_pairing(self, mac_address: str) -> bool:
        """Remove existing pairing for controller"""
        self._log(f"Removing existing pairing for {mac_address}...", Colors.YELLOW)
        
        try:
            # Disconnect first
            self._run_command(["bluetoothctl", "disconnect", mac_address])
            time.sleep(1)
            
            # Remove pairing
            result = self._run_command(["bluetoothctl", "remove", mac_address])
            if result.returncode == 0:
                self._log("✓ Existing pairing removed", Colors.GREEN)
                return True
            else:
                self._log("⚠️  Could not remove existing pairing", Colors.YELLOW)
                return False
        except:
            self._log("⚠️  Could not remove existing pairing", Colors.YELLOW)
            return False
    
    def pair_controller(self, mac_address: str) -> bool:
        """Pair with controller using advanced method"""
        self._log(f"Pairing with controller {mac_address}...", Colors.YELLOW)
        
        # Check if already paired
        try:
            result = self._run_command(["bluetoothctl", "info", mac_address])
            if result.returncode == 0 and "Paired: yes" in result.stdout:
                self._log("✓ Controller already paired", Colors.GREEN)
                return True
        except:
            pass
        
        # Try pairing multiple times with different approaches
        for attempt in range(1, self.max_retries + 1):
            self._log(f"Pairing attempt {attempt}/{self.max_retries}...", Colors.CYAN)
            
            try:
                # Method 1: Standard pairing
                if attempt <= 2:
                    result = self._run_command(["bluetoothctl", "pair", mac_address], 
                                             timeout=self.pair_timeout)
                    if result.returncode == 0:
                        self._log("✓ Controller paired successfully", Colors.GREEN)
                        return True
                
                # Method 2: Connect first, then pair (some controllers prefer this)
                elif attempt == 3:
                    self._log("Trying connect-first method...", Colors.CYAN)
                    connect_result = self._run_command(["bluetoothctl", "connect", mac_address], 
                                                     timeout=self.connect_timeout)
                    time.sleep(2)
                    
                    pair_result = self._run_command(["bluetoothctl", "pair", mac_address], 
                                                  timeout=self.pair_timeout)
                    if pair_result.returncode == 0:
                        self._log("✓ Controller paired successfully", Colors.GREEN)
                        return True
                
                # Method 3: Reset and retry
                elif attempt == 4:
                    self._log("Resetting Bluetooth and retrying...", Colors.CYAN)
                    self.reset_bluetooth_stack()
                    time.sleep(2)
                    self.prepare_for_pairing()
                    
                    result = self._run_command(["bluetoothctl", "pair", mac_address], 
                                             timeout=self.pair_timeout)
                    if result.returncode == 0:
                        self._log("✓ Controller paired successfully", Colors.GREEN)
                        return True
                
                # Method 4: Manual authorization
                else:
                    self._log("Trying manual authorization...", Colors.CYAN)
                    # This is a last resort - might need user interaction
                    result = self._run_command(["bluetoothctl", "pair", mac_address], 
                                             timeout=self.pair_timeout)
                    if result.returncode == 0:
                        self._log("✓ Controller paired successfully", Colors.GREEN)
                        return True
                
                self._log(f"❌ Pairing attempt {attempt} failed", Colors.RED)
                if attempt < self.max_retries:
                    self._log("Retrying in 3 seconds...", Colors.YELLOW)
                    time.sleep(3)
                    
            except Exception as e:
                self._log(f"❌ Pairing attempt {attempt} failed: {e}", Colors.RED)
                if attempt < self.max_retries:
                    time.sleep(3)
        
        self._log(f"❌ Failed to pair controller after {self.max_retries} attempts", Colors.RED)
        return False
    
    def trust_controller(self, mac_address: str) -> bool:
        """Trust the controller"""
        self._log(f"Trusting controller {mac_address}...", Colors.YELLOW)
        
        try:
            result = self._run_command(["bluetoothctl", "trust", mac_address])
            if result.returncode == 0:
                self._log("✓ Controller trusted", Colors.GREEN)
                return True
            else:
                self._log("❌ Failed to trust controller", Colors.RED)
                return False
        except:
            self._log("❌ Failed to trust controller", Colors.RED)
            return False
    
    def connect_controller(self, mac_address: str) -> bool:
        """Connect to the controller"""
        self._log(f"Connecting to controller {mac_address}...", Colors.YELLOW)
        
        # Check if already connected
        try:
            result = self._run_command(["bluetoothctl", "info", mac_address])
            if result.returncode == 0 and "Connected: yes" in result.stdout:
                self._log("✓ Controller already connected", Colors.GREEN)
                return True
        except:
            pass
        
        # Try connecting
        for attempt in range(1, self.max_retries + 1):
            self._log(f"Connection attempt {attempt}/{self.max_retries}...", Colors.CYAN)
            
            try:
                result = self._run_command(["bluetoothctl", "connect", mac_address], 
                                         timeout=self.connect_timeout)
                if result.returncode == 0:
                    self._log("✓ Controller connected successfully", Colors.GREEN)
                    return True
                else:
                    self._log(f"❌ Connection attempt {attempt} failed", Colors.RED)
                    if attempt < self.max_retries:
                        self._log("Retrying in 2 seconds...", Colors.YELLOW)
                        time.sleep(2)
            except:
                self._log(f"❌ Connection attempt {attempt} failed", Colors.RED)
                if attempt < self.max_retries:
                    time.sleep(2)
        
        self._log(f"❌ Failed to connect controller after {self.max_retries} attempts", Colors.RED)
        return False
    
    def test_controller(self, mac_address: str) -> bool:
        """Test controller functionality"""
        self._log("Testing controller functionality...", Colors.YELLOW)
        
        # Wait for device to be ready
        time.sleep(3)
        
        # Check for joystick device
        try:
            result = subprocess.run(["ls", "/dev/input/js*"], capture_output=True, text=True)
            if result.returncode == 0:
                js_devices = result.stdout.strip().split('\n')
                self._log(f"✓ Joystick device found: {js_devices[0]}", Colors.GREEN)
                
                # Test input for a few seconds
                self._log("Testing controller input (5 seconds)...", Colors.CYAN)
                self._log("Press buttons and move sticks to test", Colors.WHITE)
                
                try:
                    test_result = subprocess.run(["timeout", "5", "jstest", "--event", js_devices[0]], 
                                               capture_output=True, text=True)
                    if test_result.returncode in [0, 124]:  # 124 is timeout exit code
                        self._log("✓ Controller input test completed", Colors.GREEN)
                        return True
                    else:
                        self._log("⚠️  Controller input test had issues", Colors.YELLOW)
                        return False
                except:
                    self._log("⚠️  Could not test controller input (jstest not available)", Colors.YELLOW)
                    return True  # Not critical
            else:
                self._log("❌ No joystick device found", Colors.RED)
                return False
        except:
            self._log("❌ Could not check for joystick device", Colors.RED)
            return False
    
    def save_controller_config(self, mac_address: str, name: str):
        """Save controller configuration"""
        config_file = os.path.expanduser("~/.doombox_controller")
        
        try:
            with open(config_file, 'w') as f:
                f.write(f"CONTROLLER_MAC={mac_address}\n")
                f.write(f"CONTROLLER_NAME={name}\n")
                f.write(f"PAIRED_DATE={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self._log(f"✓ Controller configuration saved to {config_file}", Colors.GREEN)
        except:
            self._log("⚠️  Could not save controller configuration", Colors.YELLOW)
    
    def show_controller_info(self, mac_address: str):
        """Show detailed controller information"""
        self._log("=" * 50, Colors.BLUE)
        self._log("  Controller Information", Colors.BLUE)
        self._log("=" * 50, Colors.BLUE)
        print()
        
        try:
            result = self._run_command(["bluetoothctl", "info", mac_address])
            if result.returncode == 0:
                info_lines = result.stdout.strip().split('\n')
                for line in info_lines:
                    if any(key in line for key in ['Name:', 'Paired:', 'Trusted:', 'Connected:', 'Battery:']):
                        self._log(f"   {line}", Colors.CYAN)
        except:
            self._log("Could not retrieve controller information", Colors.YELLOW)
        
        # Check for input devices
        print()
        self._log("Joystick Devices:", Colors.CYAN)
        try:
            result = subprocess.run(["ls", "-l", "/dev/input/js*"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    self._log(f"   {line}", Colors.WHITE)
            else:
                self._log("   None found", Colors.WHITE)
        except:
            self._log("   Could not check", Colors.WHITE)
        
        print()
    
    def show_final_status(self, success: bool, mac_address: str = None):
        """Show final pairing status"""
        self._log("=" * 60, Colors.BLUE)
        self._log("  Final Status", Colors.BLUE)
        self._log("=" * 60, Colors.BLUE)
        print()
        
        if success and mac_address:
            self._log("🎮 SUCCESS! Your DualShock 4 controller is ready to use!", Colors.GREEN)
            print()
            self._log("Next steps:", Colors.CYAN)
            self._log("   • Your controller should now work with DoomBox", Colors.WHITE)
            self._log("   • Try the Konami code: ↑↑↓↓←→←→BA", Colors.WHITE)
            self._log("   • The controller should auto-connect on reboot", Colors.WHITE)
            print()
            self._log("Controller will be saved for auto-connection", Colors.GREEN)
        else:
            self._log("❌ Controller pairing failed", Colors.RED)
            print()
            self._log("Troubleshooting:", Colors.YELLOW)
            self._log("   • Make sure controller is in pairing mode", Colors.WHITE)
            self._log("   • Reset controller (small button on back)", Colors.WHITE)
            self._log("   • Try connecting via USB cable first", Colors.WHITE)
            self._log("   • Check Bluetooth service: systemctl status bluetooth", Colors.WHITE)
            self._log("   • Try: sudo systemctl restart bluetooth", Colors.WHITE)
            self._log("   • Run this script again with --verbose flag", Colors.WHITE)
    
    def pair_controller_interactive(self, force_unpair: bool = False, specific_mac: str = None):
        """Main interactive pairing process"""
        self._log("=" * 60, Colors.BLUE)
        self._log("  DoomBox Advanced Controller Pairing", Colors.BLUE)
        self._log("=" * 60, Colors.BLUE)
        print()
        
        # Check system prerequisites
        if not self.check_dependencies():
            return False
        
        if not self.check_bluetooth_service():
            return False
        
        if not self.check_bluetooth_hardware():
            return False
        
        if not self.prepare_for_pairing():
            return False
        
        # Show pairing instructions if not using specific MAC
        if not specific_mac:
            self.show_pairing_instructions()
        
        # Scan for controllers or use specific MAC
        if specific_mac:
            controllers = [{'mac': specific_mac, 'name': 'Specified Controller'}]
        else:
            controllers = self.scan_for_controllers()
        
        if not controllers:
            self.show_final_status(False)
            return False
        
        # Select controller (use first if only one)
        if len(controllers) == 1:
            selected_controller = controllers[0]
        else:
            self._log("Multiple controllers found:", Colors.YELLOW)
            for i, controller in enumerate(controllers):
                self._log(f"   {i+1}. {controller['mac']} ({controller['name']})", Colors.WHITE)
            
            while True:
                try:
                    choice = input(f"\n{Colors.CYAN}Select controller (1-{len(controllers)}): {Colors.NC}")
                    idx = int(choice) - 1
                    if 0 <= idx < len(controllers):
                        selected_controller = controllers[idx]
                        break
                    else:
                        self._log("Invalid selection", Colors.RED)
                except (ValueError, KeyboardInterrupt):
                    self._log("Invalid input", Colors.RED)
                    continue
        
        mac_address = selected_controller['mac']
        controller_name = selected_controller['name']
        
        self._log(f"Selected controller: {mac_address} ({controller_name})", Colors.GREEN)
        
        # Remove existing pairing if requested
        if force_unpair:
            self.remove_existing_pairing(mac_address)
        
        # Pair controller
        if not self.pair_controller(mac_address):
            self.show_final_status(False)
            return False
        
        # Trust controller
        if not self.trust_controller(mac_address):
            self._log("⚠️  Controller pairing succeeded but trust failed", Colors.YELLOW)
        
        # Connect controller
        if not self.connect_controller(mac_address):
            self.show_final_status(False)
            return False
        
        # Test controller
        test_success = self.test_controller(mac_address)
        if not test_success:
            self._log("⚠️  Controller connected but testing failed", Colors.YELLOW)
        
        # Save configuration
        self.save_controller_config(mac_address, controller_name)
        
        # Show controller info
        self.show_controller_info(mac_address)
        
        # Show final status
        self.show_final_status(True, mac_address)
        
        return True

def main():
    """Main script entry point"""
    parser = argparse.ArgumentParser(description='Advanced DualShock 4 Controller Pairing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--force', '-f', action='store_true', help='Force unpair and re-pair existing controller')
    parser.add_argument('--mac', type=str, help='Specify controller MAC address directly')
    parser.add_argument('--scan-only', action='store_true', help='Only scan for controllers, don\'t pair')
    
    args = parser.parse_args()
    
    # Create pairing manager
    pairing_manager = ControllerPairing(verbose=args.verbose)
    
    try:
        if args.scan_only:
            # Just scan and show results
            pairing_manager._log("Scanning for controllers only...", Colors.YELLOW)
            pairing_manager.prepare_for_pairing()
            pairing_manager.show_pairing_instructions()
            controllers = pairing_manager.scan_for_controllers()
            
            if controllers:
                pairing_manager._log(f"Found {len(controllers)} controller(s):", Colors.GREEN)
                for controller in controllers:
                    pairing_manager._log(f"   • {controller['mac']} ({controller['name']})", Colors.WHITE)
            else:
                pairing_manager._log("No controllers found", Colors.RED)
        else:
            # Full pairing process
            success = pairing_manager.pair_controller_interactive(
                force_unpair=args.force,
                specific_mac=args.mac
            )
            
            if success:
                sys.exit(0)
            else:
                sys.exit(1)
    
    except KeyboardInterrupt:
        pairing_manager._log("\nScript interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        pairing_manager._log(f"Unexpected error: {e}", Colors.RED)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        pairing_manager._cleanup()

if __name__ == "__main__":
    main()
