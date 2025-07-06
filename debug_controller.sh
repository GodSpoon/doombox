#!/bin/bash

# DoomBox Controller Debug and Test Script
# Tests DualShock 4 controller functionality and connection
# Provides detailed debugging information

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="DoomBox Controller Debug"

echo -e "${BLUE}=========================================="
echo -e "  ${SCRIPT_NAME} v${SCRIPT_VERSION}"
echo -e "  Controller Testing & Debugging"
echo -e "==========================================${NC}"
echo ""

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -t, --test-input    Test controller input for 30 seconds"
    echo "  -p, --pygame-test   Test with Python/pygame"
    echo "  -s, --status        Show controller status only"
    echo "  -c, --continuous    Continuous monitoring mode"
    echo "  -v, --verbose       Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                  # Full debug report"
    echo "  $0 --test-input     # Test controller input"
    echo "  $0 --pygame-test    # Test with pygame"
    echo "  $0 --status         # Quick status check"
    echo ""
}

# Function to check system status
check_system_status() {
    echo -e "${YELLOW}System Status Check${NC}"
    echo -e "===================="
    echo ""
    
    # Check Bluetooth service
    echo -e "${CYAN}Bluetooth Service:${NC}"
    if systemctl is-active --quiet bluetooth; then
        echo -e "   Status: ${GREEN}Active${NC}"
        echo -e "   Enabled: $(systemctl is-enabled bluetooth 2>/dev/null || echo 'Unknown')"
    else
        echo -e "   Status: ${RED}Inactive${NC}"
    fi
    
    # Check Bluetooth adapter
    echo -e "${CYAN}Bluetooth Adapter:${NC}"
    if hciconfig hci0 2>/dev/null | grep -q "UP RUNNING"; then
        echo -e "   Status: ${GREEN}Up and Running${NC}"
        hciconfig hci0 | grep -E "(BD Address|Class|Features)" | sed 's/^/   /'
    else
        echo -e "   Status: ${RED}Down or Not Found${NC}"
    fi
    
    # Check for controller processes
    echo -e "${CYAN}Controller Processes:${NC}"
    local processes=$(ps aux | grep -i "controller\|bluetooth\|joystick" | grep -v grep)
    if [ -n "$processes" ]; then
        echo "$processes" | sed 's/^/   /'
    else
        echo -e "   ${YELLOW}No controller-related processes found${NC}"
    fi
    
    echo ""
}

# Function to check Bluetooth devices
check_bluetooth_devices() {
    echo -e "${YELLOW}Bluetooth Devices${NC}"
    echo -e "================="
    echo ""
    
    # List all devices
    echo -e "${CYAN}All Bluetooth Devices:${NC}"
    local devices=$(bluetoothctl devices 2>/dev/null)
    if [ -n "$devices" ]; then
        echo "$devices" | sed 's/^/   /'
    else
        echo -e "   ${YELLOW}No devices found${NC}"
    fi
    
    # List connected devices
    echo -e "${CYAN}Connected Devices:${NC}"
    local connected=$(bluetoothctl devices Connected 2>/dev/null)
    if [ -n "$connected" ]; then
        echo "$connected" | sed 's/^/   /'
    else
        echo -e "   ${YELLOW}No connected devices${NC}"
    fi
    
    # List paired devices
    echo -e "${CYAN}Paired Devices:${NC}"
    local paired=$(bluetoothctl devices Paired 2>/dev/null)
    if [ -n "$paired" ]; then
        echo "$paired" | sed 's/^/   /'
    else
        echo -e "   ${YELLOW}No paired devices${NC}"
    fi
    
    echo ""
}

# Function to check controller-specific info
check_controller_info() {
    echo -e "${YELLOW}Controller Information${NC}"
    echo -e "====================="
    echo ""
    
    # Look for DualShock 4 controllers
    local ds4_devices=$(bluetoothctl devices 2>/dev/null | grep -i "wireless controller\|dualshock\|ds4\|controller")
    
    if [ -n "$ds4_devices" ]; then
        echo -e "${CYAN}DualShock 4 Controllers Found:${NC}"
        echo "$ds4_devices" | sed 's/^/   /'
        echo ""
        
        # Get detailed info for each controller
        echo "$ds4_devices" | while read -r line; do
            local mac=$(echo "$line" | grep -oE "([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")
            if [ -n "$mac" ]; then
                echo -e "${CYAN}Controller Details ($mac):${NC}"
                bluetoothctl info "$mac" 2>/dev/null | sed 's/^/   /' || echo -e "   ${RED}Could not get info${NC}"
                echo ""
            fi
        done
    else
        echo -e "${YELLOW}No DualShock 4 controllers found${NC}"
    fi
}

# Function to check input devices
check_input_devices() {
    echo -e "${YELLOW}Input Devices${NC}"
    echo -e "============="
    echo ""
    
    # Check joystick devices
    echo -e "${CYAN}Joystick Devices:${NC}"
    if ls /dev/input/js* >/dev/null 2>&1; then
        for js in /dev/input/js*; do
            echo -e "   Device: $js"
            # Get device info if available
            local info=$(udevadm info --query=property --name="$js" 2>/dev/null | grep -E "ID_INPUT|ID_MODEL|ID_VENDOR" || true)
            if [ -n "$info" ]; then
                echo "$info" | sed 's/^/      /'
            fi
        done
    else
        echo -e "   ${YELLOW}No joystick devices found${NC}"
    fi
    
    # Check event devices
    echo -e "${CYAN}Event Devices:${NC}"
    if ls /dev/input/event* >/dev/null 2>&1; then
        for event in /dev/input/event*; do
            local name=$(cat "/sys/class/input/$(basename "$event")/device/name" 2>/dev/null || echo "Unknown")
            echo -e "   $event: $name"
        done
    else
        echo -e "   ${YELLOW}No event devices found${NC}"
    fi
    
    echo ""
}

# Function to test controller input
test_controller_input() {
    echo -e "${YELLOW}Controller Input Test${NC}"
    echo -e "===================="
    echo ""
    
    # Find joystick device
    if ls /dev/input/js* >/dev/null 2>&1; then
        local js_device=$(ls /dev/input/js* | head -1)
        echo -e "${CYAN}Testing device: $js_device${NC}"
        echo ""
        echo -e "${GREEN}Press buttons and move sticks...${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        echo ""
        
        # Test with jstest
        jstest "$js_device" 2>/dev/null || {
            echo -e "${RED}❌ jstest failed${NC}"
            echo -e "${YELLOW}Try: sudo apt install joystick${NC}"
            return 1
        }
    else
        echo -e "${RED}❌ No joystick devices found${NC}"
        echo -e "${YELLOW}Make sure your controller is connected${NC}"
        return 1
    fi
}

# Function to test with pygame
test_pygame_controller() {
    echo -e "${YELLOW}Pygame Controller Test${NC}"
    echo -e "====================="
    echo ""
    
    # Check if pygame is available
    if ! python3 -c "import pygame" 2>/dev/null; then
        echo -e "${RED}❌ pygame not available${NC}"
        echo -e "${YELLOW}Install with: pip install pygame${NC}"
        return 1
    fi
    
    echo -e "${CYAN}Running pygame controller test...${NC}"
    echo ""
    
    # Create and run pygame test
    python3 << 'EOF'
import pygame
import sys

def test_controller():
    pygame.init()
    pygame.joystick.init()
    
    print(f"Pygame version: {pygame.version.ver}")
    print(f"Number of joysticks: {pygame.joystick.get_count()}")
    
    if pygame.joystick.get_count() == 0:
        print("❌ No joysticks found")
        return False
    
    # Initialize first joystick
    joy = pygame.joystick.Joystick(0)
    joy.init()
    
    print(f"✓ Joystick initialized:")
    print(f"   Name: {joy.get_name()}")
    print(f"   Buttons: {joy.get_numbuttons()}")
    print(f"   Axes: {joy.get_numaxes()}")
    print(f"   Hats: {joy.get_numhats()}")
    print(f"   Balls: {joy.get_numballs()}")
    
    # Test input for 10 seconds
    print(f"\n🎮 Testing input for 10 seconds...")
    print("   Press buttons and move sticks!")
    
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    
    try:
        while pygame.time.get_ticks() - start_time < 10000:  # 10 seconds
            pygame.event.pump()
            
            # Check for button presses
            for i in range(joy.get_numbuttons()):
                if joy.get_button(i):
                    print(f"   Button {i} pressed")
            
            # Check axes
            for i in range(joy.get_numaxes()):
                axis_value = joy.get_axis(i)
                if abs(axis_value) > 0.1:  # Dead zone
                    print(f"   Axis {i}: {axis_value:.2f}")
            
            # Check hat
            for i in range(joy.get_numhats()):
                hat_value = joy.get_hat(i)
                if hat_value != (0, 0):
                    print(f"   Hat {i}: {hat_value}")
            
            clock.tick(30)  # 30 FPS
            
    except KeyboardInterrupt:
        print("\n   Test interrupted by user")
    
    print("✓ Pygame test completed")
    pygame.quit()
    return True

if __name__ == "__main__":
    test_controller()
EOF
}

# Function to monitor controller continuously
monitor_controller() {
    echo -e "${YELLOW}Continuous Controller Monitor${NC}"
    echo -e "============================"
    echo ""
    echo -e "${CYAN}Monitoring controller status...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    local last_status=""
    
    while true; do
        # Check Bluetooth connection
        local bt_status="Disconnected"
        local js_status="Not Found"
        
        # Check for connected controllers
        if bluetoothctl devices Connected 2>/dev/null | grep -qi "controller"; then
            bt_status="Connected"
        fi
        
        # Check for joystick devices
        if ls /dev/input/js* >/dev/null 2>&1; then
            js_status="Available"
        fi
        
        local current_status="BT: $bt_status, JS: $js_status"
        
        if [ "$current_status" != "$last_status" ]; then
            echo -e "[$(date '+%H:%M:%S')] ${CYAN}$current_status${NC}"
            last_status="$current_status"
        fi
        
        sleep 2
    done
}

# Function to show quick status
show_quick_status() {
    echo -e "${YELLOW}Quick Status Check${NC}"
    echo -e "=================="
    echo ""
    
    # Bluetooth service
    if systemctl is-active --quiet bluetooth; then
        echo -e "${GREEN}✓${NC} Bluetooth service running"
    else
        echo -e "${RED}❌${NC} Bluetooth service not running"
    fi
    
    # Bluetooth adapter
    if hciconfig hci0 2>/dev/null | grep -q "UP RUNNING"; then
        echo -e "${GREEN}✓${NC} Bluetooth adapter active"
    else
        echo -e "${RED}❌${NC} Bluetooth adapter not active"
    fi
    
    # Connected controllers
    local controllers=$(bluetoothctl devices Connected 2>/dev/null | grep -i "controller" | wc -l)
    if [ "$controllers" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} $controllers controller(s) connected via Bluetooth"
    else
        echo -e "${YELLOW}⚠️${NC} No controllers connected via Bluetooth"
    fi
    
    # Joystick devices
    local joysticks=$(ls /dev/input/js* 2>/dev/null | wc -l)
    if [ "$joysticks" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} $joysticks joystick device(s) available"
    else
        echo -e "${RED}❌${NC} No joystick devices found"
    fi
    
    echo ""
}

# Function to run full debug
run_full_debug() {
    check_system_status
    check_bluetooth_devices
    check_controller_info
    check_input_devices
    
    echo -e "${BLUE}=========================================="
    echo -e "  Debug Report Complete"
    echo -e "==========================================${NC}"
    echo ""
    echo -e "${CYAN}Summary:${NC}"
    show_quick_status
    
    echo -e "${YELLOW}If you need to pair a controller, run:${NC}"
    echo -e "   ./pair_controller.sh"
    echo ""
    echo -e "${YELLOW}To test controller input, run:${NC}"
    echo -e "   $0 --test-input"
    echo ""
}

# Main function
main() {
    local test_input=false
    local pygame_test=false
    local status_only=false
    local continuous=false
    local verbose=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--test-input)
                test_input=true
                shift
                ;;
            -p|--pygame-test)
                pygame_test=true
                shift
                ;;
            -s|--status)
                status_only=true
                shift
                ;;
            -c|--continuous)
                continuous=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
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
    
    # Handle specific modes
    if [ "$status_only" = true ]; then
        show_quick_status
        exit 0
    fi
    
    if [ "$test_input" = true ]; then
        test_controller_input
        exit 0
    fi
    
    if [ "$pygame_test" = true ]; then
        test_pygame_controller
        exit 0
    fi
    
    if [ "$continuous" = true ]; then
        monitor_controller
        exit 0
    fi
    
    # Run full debug by default
    run_full_debug
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Monitoring stopped${NC}"; exit 0' INT TERM

# Run main function
main "$@"
