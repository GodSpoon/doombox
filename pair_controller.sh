#!/bin/bash

# DoomBox DualShock 4 Controller Pairing Script
# Pairs and connects a DualShock 4 controller via Bluetooth
# Compatible with Radxa Zero and similar ARM devices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script info
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="DoomBox Controller Pairing"

# Configuration
CONTROLLER_NAME="Sony Interactive Entertainment Wireless Controller"
CONTROLLER_MAC_PREFIX="00:1B:DC"  # Common DS4 MAC prefix (may vary)
SCAN_TIMEOUT=30
PAIR_TIMEOUT=15
CONNECT_TIMEOUT=10
MAX_RETRIES=3

# Global variables
CONTROLLER_MAC=""
BLUETOOTH_AVAILABLE=false
CONTROLLER_FOUND=false
CONTROLLER_PAIRED=false
CONTROLLER_CONNECTED=false

echo -e "${BLUE}=========================================="
echo -e "  ${SCRIPT_NAME} v${SCRIPT_VERSION}"
echo -e "  DualShock 4 Bluetooth Setup"
echo -e "==========================================${NC}"
echo ""

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -s, --scan-only     Only scan for controllers, don't pair"
    echo "  -f, --force         Force unpair and re-pair if already paired"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -t, --timeout SEC   Set scan timeout (default: 30 seconds)"
    echo "  --mac MAC_ADDR      Specify controller MAC address directly"
    echo ""
    echo "Examples:"
    echo "  $0                  # Standard pairing process"
    echo "  $0 --scan-only      # Just scan for controllers"
    echo "  $0 --force          # Force re-pair existing controller"
    echo "  $0 --mac 12:34:56:78:90:AB  # Pair specific MAC address"
    echo ""
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  Running as root - this is usually not necessary${NC}"
        echo -e "   You may want to run this script as a regular user"
        echo -e "   Press Ctrl+C to cancel, or Enter to continue..."
        read -r
    fi
}

# Function to check system dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking system dependencies...${NC}"
    
    local missing_deps=()
    
    # Check for required commands
    command -v bluetoothctl >/dev/null || missing_deps+=("bluetoothctl (bluez)")
    command -v hciconfig >/dev/null || missing_deps+=("hciconfig (bluez-tools)")
    command -v sdptool >/dev/null || missing_deps+=("sdptool (bluez-tools)")
    command -v jstest >/dev/null || missing_deps+=("jstest (joystick)")
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing dependencies:${NC}"
        for dep in "${missing_deps[@]}"; do
            echo -e "   • $dep"
        done
        echo ""
        echo -e "${YELLOW}Install missing dependencies with:${NC}"
        echo -e "   sudo apt update"
        echo -e "   sudo apt install -y bluetooth bluez bluez-tools joystick jstest-gtk"
        echo ""
        return 1
    fi
    
    echo -e "${GREEN}✓ All dependencies found${NC}"
    return 0
}

# Function to check Bluetooth service
check_bluetooth_service() {
    echo -e "${YELLOW}Checking Bluetooth service...${NC}"
    
    # Check if bluetooth service is running
    if ! systemctl is-active --quiet bluetooth; then
        echo -e "${RED}❌ Bluetooth service is not running${NC}"
        echo -e "${YELLOW}Starting Bluetooth service...${NC}"
        
        if sudo systemctl start bluetooth 2>/dev/null; then
            echo -e "${GREEN}✓ Bluetooth service started${NC}"
        else
            echo -e "${RED}❌ Failed to start Bluetooth service${NC}"
            echo -e "   Try: sudo systemctl start bluetooth"
            return 1
        fi
    else
        echo -e "${GREEN}✓ Bluetooth service is running${NC}"
    fi
    
    # Check if bluetooth is enabled
    if ! systemctl is-enabled --quiet bluetooth; then
        echo -e "${YELLOW}Enabling Bluetooth service for auto-start...${NC}"
        sudo systemctl enable bluetooth
        echo -e "${GREEN}✓ Bluetooth service enabled${NC}"
    fi
    
    BLUETOOTH_AVAILABLE=true
    return 0
}

# Function to check Bluetooth adapter
check_bluetooth_adapter() {
    echo -e "${YELLOW}Checking Bluetooth adapter...${NC}"
    
    # Check if adapter is up
    if ! hciconfig hci0 up 2>/dev/null; then
        echo -e "${RED}❌ Bluetooth adapter not found or not working${NC}"
        echo -e "   Common issues:"
        echo -e "   • Bluetooth hardware not available"
        echo -e "   • Driver not loaded"
        echo -e "   • Adapter powered off"
        echo ""
        echo -e "${YELLOW}Trying to enable adapter...${NC}"
        
        # Try to power on the adapter
        if sudo hciconfig hci0 up 2>/dev/null; then
            echo -e "${GREEN}✓ Bluetooth adapter enabled${NC}"
        else
            echo -e "${RED}❌ Could not enable Bluetooth adapter${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✓ Bluetooth adapter is working${NC}"
    fi
    
    # Show adapter info
    local adapter_info=$(hciconfig hci0 2>/dev/null | head -1)
    if [ -n "$adapter_info" ]; then
        echo -e "${CYAN}   Adapter: $adapter_info${NC}"
    fi
    
    return 0
}

# Function to prepare controller for pairing
prepare_controller() {
    echo -e "${BLUE}=========================================="
    echo -e "  Controller Preparation"
    echo -e "==========================================${NC}"
    echo ""
    echo -e "${YELLOW}Prepare your DualShock 4 controller:${NC}"
    echo ""
    echo -e "1. ${CYAN}Turn OFF${NC} your controller completely"
    echo -e "   (Hold PS button for 10 seconds if needed)"
    echo ""
    echo -e "2. ${CYAN}Enter pairing mode${NC} by holding:"
    echo -e "   ${YELLOW}PS button + Share button${NC}"
    echo -e "   for about 3-5 seconds"
    echo ""
    echo -e "3. The controller light bar should start ${CYAN}flashing white${NC}"
    echo -e "   (This means it's in pairing mode)"
    echo ""
    echo -e "4. Keep the controller close to your device"
    echo -e "   (within 1-2 meters)"
    echo ""
    echo -e "${GREEN}Press Enter when your controller is flashing white...${NC}"
    read -r
}

# Function to scan for controllers
scan_for_controllers() {
    echo -e "${YELLOW}Scanning for DualShock 4 controllers...${NC}"
    echo -e "${CYAN}Timeout: ${SCAN_TIMEOUT} seconds${NC}"
    echo ""
    
    # Start scanning
    {
        echo "scan on"
        sleep $SCAN_TIMEOUT
        echo "scan off"
    } | bluetoothctl &
    
    local bt_pid=$!
    
    # Monitor for controller discovery
    local found_controllers=()
    local scan_start=$(date +%s)
    
    while [ $(($(date +%s) - scan_start)) -lt $SCAN_TIMEOUT ]; do
        # Check for new devices
        local devices=$(bluetoothctl devices 2>/dev/null | grep -i "wireless controller\|dualshock\|ds4\|controller" || true)
        
        if [ -n "$devices" ]; then
            echo -e "${GREEN}✓ Found controller(s):${NC}"
            echo "$devices" | while read -r line; do
                echo -e "${CYAN}   $line${NC}"
                
                # Extract MAC address
                local mac=$(echo "$line" | grep -oE "([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")
                if [ -n "$mac" ]; then
                    found_controllers+=("$mac")
                    CONTROLLER_MAC="$mac"
                    CONTROLLER_FOUND=true
                fi
            done
            break
        fi
        
        # Show progress
        local elapsed=$(($(date +%s) - scan_start))
        local remaining=$((SCAN_TIMEOUT - elapsed))
        printf "\r${YELLOW}Scanning... ${remaining}s remaining${NC}"
        
        sleep 1
    done
    
    # Stop scanning
    kill $bt_pid 2>/dev/null || true
    wait $bt_pid 2>/dev/null || true
    
    echo ""
    
    if [ "$CONTROLLER_FOUND" = true ]; then
        echo -e "${GREEN}✓ Controller found: $CONTROLLER_MAC${NC}"
        return 0
    else
        echo -e "${RED}❌ No controllers found${NC}"
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo -e "   • Make sure controller is in pairing mode (flashing white)"
        echo -e "   • Try resetting controller (small button on back)"
        echo -e "   • Move controller closer to device"
        echo -e "   • Check if controller is already paired to another device"
        return 1
    fi
}

# Function to pair controller
pair_controller() {
    echo -e "${YELLOW}Pairing with controller $CONTROLLER_MAC...${NC}"
    
    # Check if already paired
    if bluetoothctl info "$CONTROLLER_MAC" 2>/dev/null | grep -q "Paired: yes"; then
        echo -e "${GREEN}✓ Controller already paired${NC}"
        CONTROLLER_PAIRED=true
        return 0
    fi
    
    # Attempt pairing
    local retry=0
    while [ $retry -lt $MAX_RETRIES ]; do
        retry=$((retry + 1))
        echo -e "${CYAN}Pairing attempt $retry/$MAX_RETRIES...${NC}"
        
        # Try to pair
        if timeout $PAIR_TIMEOUT bluetoothctl pair "$CONTROLLER_MAC" 2>/dev/null; then
            echo -e "${GREEN}✓ Controller paired successfully${NC}"
            CONTROLLER_PAIRED=true
            return 0
        else
            echo -e "${RED}❌ Pairing attempt $retry failed${NC}"
            if [ $retry -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}Retrying in 2 seconds...${NC}"
                sleep 2
            fi
        fi
    done
    
    echo -e "${RED}❌ Failed to pair controller after $MAX_RETRIES attempts${NC}"
    return 1
}

# Function to trust controller
trust_controller() {
    echo -e "${YELLOW}Trusting controller $CONTROLLER_MAC...${NC}"
    
    if bluetoothctl trust "$CONTROLLER_MAC" 2>/dev/null; then
        echo -e "${GREEN}✓ Controller trusted${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to trust controller${NC}"
        return 1
    fi
}

# Function to connect controller
connect_controller() {
    echo -e "${YELLOW}Connecting to controller $CONTROLLER_MAC...${NC}"
    
    # Check if already connected
    if bluetoothctl info "$CONTROLLER_MAC" 2>/dev/null | grep -q "Connected: yes"; then
        echo -e "${GREEN}✓ Controller already connected${NC}"
        CONTROLLER_CONNECTED=true
        return 0
    fi
    
    # Attempt connection
    local retry=0
    while [ $retry -lt $MAX_RETRIES ]; do
        retry=$((retry + 1))
        echo -e "${CYAN}Connection attempt $retry/$MAX_RETRIES...${NC}"
        
        # Try to connect
        if timeout $CONNECT_TIMEOUT bluetoothctl connect "$CONTROLLER_MAC" 2>/dev/null; then
            echo -e "${GREEN}✓ Controller connected successfully${NC}"
            CONTROLLER_CONNECTED=true
            return 0
        else
            echo -e "${RED}❌ Connection attempt $retry failed${NC}"
            if [ $retry -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}Retrying in 2 seconds...${NC}"
                sleep 2
            fi
        fi
    done
    
    echo -e "${RED}❌ Failed to connect controller after $MAX_RETRIES attempts${NC}"
    return 1
}

# Function to test controller
test_controller() {
    echo -e "${BLUE}=========================================="
    echo -e "  Controller Testing"
    echo -e "==========================================${NC}"
    echo ""
    echo -e "${YELLOW}Testing controller functionality...${NC}"
    
    # Wait for device to be ready
    sleep 3
    
    # Check for joystick device
    if ls /dev/input/js* >/dev/null 2>&1; then
        local js_device=$(ls /dev/input/js* | head -1)
        echo -e "${GREEN}✓ Joystick device found: $js_device${NC}"
        
        # Test with jstest
        echo -e "${CYAN}Testing controller input (10 seconds)...${NC}"
        echo -e "${YELLOW}Press buttons and move sticks to test${NC}"
        echo ""
        
        if timeout 10 jstest "$js_device" 2>/dev/null; then
            echo -e "${GREEN}✓ Controller input test completed${NC}"
        else
            echo -e "${YELLOW}⚠️  Controller input test timed out${NC}"
        fi
    else
        echo -e "${RED}❌ No joystick device found${NC}"
        echo -e "${YELLOW}The controller may not be fully functional${NC}"
        return 1
    fi
    
    return 0
}

# Function to show controller info
show_controller_info() {
    echo -e "${BLUE}=========================================="
    echo -e "  Controller Information"
    echo -e "==========================================${NC}"
    echo ""
    
    if [ -n "$CONTROLLER_MAC" ]; then
        echo -e "${CYAN}Controller MAC Address:${NC} $CONTROLLER_MAC"
        
        # Get detailed info from bluetoothctl
        local info=$(bluetoothctl info "$CONTROLLER_MAC" 2>/dev/null)
        if [ -n "$info" ]; then
            echo -e "${CYAN}Name:${NC} $(echo "$info" | grep "Name:" | cut -d' ' -f2-)"
            echo -e "${CYAN}Paired:${NC} $(echo "$info" | grep "Paired:" | cut -d' ' -f2)"
            echo -e "${CYAN}Trusted:${NC} $(echo "$info" | grep "Trusted:" | cut -d' ' -f2)"
            echo -e "${CYAN}Connected:${NC} $(echo "$info" | grep "Connected:" | cut -d' ' -f2)"
            echo -e "${CYAN}Battery:${NC} $(echo "$info" | grep "Battery" | cut -d' ' -f2- || echo "Unknown")"
        fi
    fi
    
    # Show joystick devices
    echo ""
    echo -e "${CYAN}Joystick Devices:${NC}"
    if ls /dev/input/js* >/dev/null 2>&1; then
        ls -l /dev/input/js* | while read -r line; do
            echo -e "   $line"
        done
    else
        echo -e "   None found"
    fi
    
    # Show event devices
    echo ""
    echo -e "${CYAN}Event Devices:${NC}"
    if ls /dev/input/event* >/dev/null 2>&1; then
        for event in /dev/input/event*; do
            local name=$(cat "/sys/class/input/$(basename "$event")/device/name" 2>/dev/null || echo "Unknown")
            echo -e "   $event: $name"
        done
    else
        echo -e "   None found"
    fi
}

# Function to save controller config
save_controller_config() {
    if [ -n "$CONTROLLER_MAC" ]; then
        local config_file="$HOME/.doombox_controller"
        echo "CONTROLLER_MAC=$CONTROLLER_MAC" > "$config_file"
        echo "CONTROLLER_NAME=$CONTROLLER_NAME" >> "$config_file"
        echo "PAIRED_DATE=$(date)" >> "$config_file"
        echo -e "${GREEN}✓ Controller configuration saved to $config_file${NC}"
    fi
}

# Function to load controller config
load_controller_config() {
    local config_file="$HOME/.doombox_controller"
    if [ -f "$config_file" ]; then
        source "$config_file"
        echo -e "${GREEN}✓ Loaded controller configuration${NC}"
        echo -e "${CYAN}   MAC: $CONTROLLER_MAC${NC}"
        return 0
    fi
    return 1
}

# Function to unpair controller
unpair_controller() {
    if [ -n "$CONTROLLER_MAC" ]; then
        echo -e "${YELLOW}Unpairing controller $CONTROLLER_MAC...${NC}"
        
        # Disconnect first
        bluetoothctl disconnect "$CONTROLLER_MAC" 2>/dev/null || true
        
        # Remove pairing
        if bluetoothctl remove "$CONTROLLER_MAC" 2>/dev/null; then
            echo -e "${GREEN}✓ Controller unpaired${NC}"
            CONTROLLER_PAIRED=false
            CONTROLLER_CONNECTED=false
            return 0
        else
            echo -e "${RED}❌ Failed to unpair controller${NC}"
            return 1
        fi
    fi
    return 1
}

# Function to show final status
show_final_status() {
    echo -e "${BLUE}=========================================="
    echo -e "  Final Status"
    echo -e "==========================================${NC}"
    echo ""
    
    if [ "$CONTROLLER_FOUND" = true ]; then
        echo -e "${GREEN}✓ Controller Found${NC}"
    else
        echo -e "${RED}❌ Controller Not Found${NC}"
    fi
    
    if [ "$CONTROLLER_PAIRED" = true ]; then
        echo -e "${GREEN}✓ Controller Paired${NC}"
    else
        echo -e "${RED}❌ Controller Not Paired${NC}"
    fi
    
    if [ "$CONTROLLER_CONNECTED" = true ]; then
        echo -e "${GREEN}✓ Controller Connected${NC}"
    else
        echo -e "${RED}❌ Controller Not Connected${NC}"
    fi
    
    echo ""
    
    if [ "$CONTROLLER_CONNECTED" = true ]; then
        echo -e "${GREEN}🎮 SUCCESS! Your DualShock 4 controller is ready to use!${NC}"
        echo ""
        echo -e "${CYAN}Next steps:${NC}"
        echo -e "   • Your controller should now work with DoomBox"
        echo -e "   • Try the Konami code: ↑↑↓↓←→←→BA"
        echo -e "   • The controller should auto-connect on reboot"
        echo ""
        echo -e "${YELLOW}If you have issues:${NC}"
        echo -e "   • Run: $0 --force (to re-pair)"
        echo -e "   • Check: systemctl status bluetooth"
        echo -e "   • Test: jstest /dev/input/js0"
    else
        echo -e "${RED}❌ Controller pairing failed${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo -e "   • Make sure controller is in pairing mode"
        echo -e "   • Reset controller (small button on back)"
        echo -e "   • Check Bluetooth service: systemctl status bluetooth"
        echo -e "   • Try: sudo systemctl restart bluetooth"
        echo -e "   • Run this script again with --force flag"
    fi
}

# Main function
main() {
    local scan_only=false
    local force=false
    local verbose=false
    local specified_mac=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--scan-only)
                scan_only=true
                shift
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -t|--timeout)
                SCAN_TIMEOUT="$2"
                shift 2
                ;;
            --mac)
                specified_mac="$2"
                shift 2
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Enable verbose mode if requested
    if [ "$verbose" = true ]; then
        set -x
    fi
    
    # Check if running as root
    check_root
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Check Bluetooth service
    if ! check_bluetooth_service; then
        exit 1
    fi
    
    # Check Bluetooth adapter
    if ! check_bluetooth_adapter; then
        exit 1
    fi
    
    # Load existing config if available
    load_controller_config || true
    
    # Use specified MAC if provided
    if [ -n "$specified_mac" ]; then
        CONTROLLER_MAC="$specified_mac"
        CONTROLLER_FOUND=true
        echo -e "${CYAN}Using specified MAC address: $CONTROLLER_MAC${NC}"
    fi
    
    # Handle force flag
    if [ "$force" = true ] && [ -n "$CONTROLLER_MAC" ]; then
        echo -e "${YELLOW}Force flag enabled - unpairing existing controller...${NC}"
        unpair_controller
    fi
    
    # If MAC is known and not scanning only, skip to pairing
    if [ -n "$CONTROLLER_MAC" ] && [ "$scan_only" = false ]; then
        echo -e "${CYAN}Using known controller MAC: $CONTROLLER_MAC${NC}"
        CONTROLLER_FOUND=true
    else
        # Prepare controller for pairing
        if [ "$scan_only" = false ]; then
            prepare_controller
        fi
        
        # Scan for controllers
        if ! scan_for_controllers; then
            exit 1
        fi
    fi
    
    # Exit if scan only
    if [ "$scan_only" = true ]; then
        show_controller_info
        exit 0
    fi
    
    # Pair controller
    if [ "$CONTROLLER_FOUND" = true ]; then
        if ! pair_controller; then
            show_final_status
            exit 1
        fi
        
        # Trust controller
        if ! trust_controller; then
            echo -e "${YELLOW}⚠️  Controller pairing succeeded but trust failed${NC}"
        fi
        
        # Connect controller
        if ! connect_controller; then
            show_final_status
            exit 1
        fi
        
        # Test controller
        test_controller
        
        # Show controller info
        show_controller_info
        
        # Save configuration
        save_controller_config
        
        # Show final status
        show_final_status
    else
        echo -e "${RED}❌ No controller found to pair${NC}"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Script interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"
