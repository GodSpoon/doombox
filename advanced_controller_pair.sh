#!/bin/bash

# DoomBox Advanced Controller Pairing Wrapper
# Provides additional functionality and troubleshooting for controller pairing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/advanced_controller_pair.py"

show_banner() {
    echo -e "${BLUE}=========================================="
    echo -e "  DoomBox Advanced Controller Pairing"
    echo -e "==========================================${NC}"
    echo ""
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -f, --force         Force unpair and re-pair existing controller"
    echo "  --mac MAC_ADDR      Specify controller MAC address directly"
    echo "  --scan-only         Only scan for controllers, don't pair"
    echo "  --troubleshoot      Run troubleshooting diagnostics"
    echo "  --status            Show current controller status"
    echo "  --reset-bluetooth   Reset Bluetooth stack"
    echo "  --install-deps      Install required dependencies"
    echo ""
    echo "Examples:"
    echo "  $0                  # Interactive pairing"
    echo "  $0 --scan-only      # Just scan for controllers"
    echo "  $0 --troubleshoot   # Run diagnostics"
    echo "  $0 --force          # Force re-pair existing controller"
    echo "  $0 --mac 20:50:E7:D2:6F:E3  # Pair specific MAC"
    echo ""
}

check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        echo -e "${YELLOW}Install with: sudo apt install python3${NC}"
        return 1
    fi
    return 0
}

install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # Update package list
    sudo apt update
    
    # Install Bluetooth and controller packages
    sudo apt install -y bluetooth bluez bluez-tools rfkill joystick jstest-gtk python3
    
    # Enable and start Bluetooth service
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
    
    # Unblock Bluetooth if blocked
    sudo rfkill unblock bluetooth
    
    # Power on Bluetooth adapter
    sudo hciconfig hci0 up 2>/dev/null || true
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

reset_bluetooth() {
    echo -e "${YELLOW}Resetting Bluetooth stack...${NC}"
    
    # Stop Bluetooth service
    sudo systemctl stop bluetooth
    sleep 2
    
    # Reset HCI interface
    sudo hciconfig hci0 down 2>/dev/null || true
    sleep 1
    sudo hciconfig hci0 up 2>/dev/null || true
    sleep 1
    
    # Clear Bluetooth cache (if it exists)
    if [ -d "/var/lib/bluetooth" ]; then
        sudo rm -rf /var/lib/bluetooth/*/cache/ 2>/dev/null || true
    fi
    
    # Restart Bluetooth service
    sudo systemctl start bluetooth
    sleep 3
    
    echo -e "${GREEN}✓ Bluetooth stack reset${NC}"
}

show_status() {
    echo -e "${YELLOW}Controller Status${NC}"
    echo -e "================="
    echo ""
    
    # Check Bluetooth service
    echo -e "${CYAN}Bluetooth Service:${NC}"
    if systemctl is-active --quiet bluetooth; then
        echo -e "   ${GREEN}✓ Running${NC}"
    else
        echo -e "   ${RED}❌ Not running${NC}"
    fi
    
    # Check Bluetooth adapter
    echo -e "${CYAN}Bluetooth Adapter:${NC}"
    if hciconfig hci0 >/dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Available${NC}"
        hciconfig hci0 | head -1 | sed 's/^/   /'
    else
        echo -e "   ${RED}❌ Not available${NC}"
    fi
    
    # Check paired devices
    echo -e "${CYAN}Paired Controllers:${NC}"
    local paired_controllers=$(bluetoothctl devices Paired 2>/dev/null | grep -i "wireless controller\|dualshock\|controller" || true)
    if [ -n "$paired_controllers" ]; then
        echo "$paired_controllers" | sed 's/^/   ✓ /'
    else
        echo -e "   ${YELLOW}None found${NC}"
    fi
    
    # Check connected devices
    echo -e "${CYAN}Connected Controllers:${NC}"
    local connected_controllers=$(bluetoothctl devices Connected 2>/dev/null | grep -i "wireless controller\|dualshock\|controller" || true)
    if [ -n "$connected_controllers" ]; then
        echo "$connected_controllers" | sed 's/^/   ✓ /'
    else
        echo -e "   ${YELLOW}None connected${NC}"
    fi
    
    # Check joystick devices
    echo -e "${CYAN}Joystick Devices:${NC}"
    if ls /dev/input/js* >/dev/null 2>&1; then
        ls -l /dev/input/js* | sed 's/^/   ✓ /'
    else
        echo -e "   ${YELLOW}None found${NC}"
    fi
    
    # Check configuration
    echo -e "${CYAN}Configuration:${NC}"
    if [ -f "$HOME/.doombox_controller" ]; then
        echo -e "   ${GREEN}✓ Controller config exists${NC}"
        cat "$HOME/.doombox_controller" | sed 's/^/      /'
    else
        echo -e "   ${YELLOW}No saved configuration${NC}"
    fi
    
    echo ""
}

run_troubleshooting() {
    echo -e "${YELLOW}Running troubleshooting diagnostics...${NC}"
    echo ""
    
    # Check system
    echo -e "${CYAN}System Check:${NC}"
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        echo -e "   ${YELLOW}⚠️  Running as root - this may cause issues${NC}"
    else
        echo -e "   ${GREEN}✓ Running as regular user${NC}"
    fi
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Python 3 available${NC}"
    else
        echo -e "   ${RED}❌ Python 3 not available${NC}"
    fi
    
    # Check required commands
    local required_commands=("bluetoothctl" "hciconfig" "rfkill" "systemctl")
    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo -e "   ${GREEN}✓ $cmd available${NC}"
        else
            echo -e "   ${RED}❌ $cmd not available${NC}"
        fi
    done
    
    echo ""
    
    # Check Bluetooth hardware
    echo -e "${CYAN}Bluetooth Hardware:${NC}"
    
    # Check rfkill
    if command -v rfkill >/dev/null 2>&1; then
        local rfkill_output=$(rfkill list bluetooth 2>/dev/null)
        if [ -n "$rfkill_output" ]; then
            if echo "$rfkill_output" | grep -q "Soft blocked: yes"; then
                echo -e "   ${RED}❌ Bluetooth soft-blocked${NC}"
                echo -e "   ${YELLOW}Fix with: sudo rfkill unblock bluetooth${NC}"
            else
                echo -e "   ${GREEN}✓ Bluetooth not blocked${NC}"
            fi
        else
            echo -e "   ${YELLOW}⚠️  No Bluetooth hardware detected${NC}"
        fi
    fi
    
    # Check HCI adapter
    if command -v hciconfig >/dev/null 2>&1; then
        if hciconfig hci0 >/dev/null 2>&1; then
            echo -e "   ${GREEN}✓ HCI adapter available${NC}"
            local hci_status=$(hciconfig hci0 2>/dev/null | grep -o "UP\|DOWN" | head -1)
            if [ "$hci_status" = "UP" ]; then
                echo -e "   ${GREEN}✓ HCI adapter is up${NC}"
            else
                echo -e "   ${YELLOW}⚠️  HCI adapter is down${NC}"
                echo -e "   ${YELLOW}Fix with: sudo hciconfig hci0 up${NC}"
            fi
        else
            echo -e "   ${RED}❌ No HCI adapter found${NC}"
        fi
    fi
    
    echo ""
    
    # Check services
    echo -e "${CYAN}Services:${NC}"
    if systemctl is-active --quiet bluetooth; then
        echo -e "   ${GREEN}✓ Bluetooth service running${NC}"
    else
        echo -e "   ${RED}❌ Bluetooth service not running${NC}"
        echo -e "   ${YELLOW}Fix with: sudo systemctl start bluetooth${NC}"
    fi
    
    if systemctl is-enabled --quiet bluetooth; then
        echo -e "   ${GREEN}✓ Bluetooth service enabled${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Bluetooth service not enabled${NC}"
        echo -e "   ${YELLOW}Fix with: sudo systemctl enable bluetooth${NC}"
    fi
    
    echo ""
    
    # Show common issues and solutions
    echo -e "${CYAN}Common Issues and Solutions:${NC}"
    echo ""
    echo -e "${YELLOW}1. Controller not found during scan:${NC}"
    echo -e "   • Make sure controller is in pairing mode (flashing white)"
    echo -e "   • Reset controller (small button on back)"
    echo -e "   • Move closer to device"
    echo -e "   • Try: $0 --reset-bluetooth"
    echo ""
    echo -e "${YELLOW}2. Pairing fails:${NC}"
    echo -e "   • Controller may be paired to another device"
    echo -e "   • Try: $0 --force"
    echo -e "   • Connect via USB cable first"
    echo -e "   • Check if controller is genuine Sony DS4"
    echo ""
    echo -e "${YELLOW}3. No joystick device:${NC}"
    echo -e "   • Controller paired but no /dev/input/js* device"
    echo -e "   • Try: sudo apt install joystick"
    echo -e "   • Disconnect and reconnect controller"
    echo ""
    echo -e "${YELLOW}4. Connection issues:${NC}"
    echo -e "   • Check Bluetooth signal strength"
    echo -e "   • Ensure controller is charged"
    echo -e "   • Try: $0 --reset-bluetooth"
    echo ""
}

# Main script logic
main() {
    show_banner
    
    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo -e "${RED}❌ Python script not found: $PYTHON_SCRIPT${NC}"
        exit 1
    fi
    
    # Check Python
    if ! check_python; then
        exit 1
    fi
    
    # Parse arguments
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        --troubleshoot)
            run_troubleshooting
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        --reset-bluetooth)
            reset_bluetooth
            exit 0
            ;;
        --install-deps)
            install_dependencies
            exit 0
            ;;
        *)
            # Pass all arguments to Python script
            exec python3 "$PYTHON_SCRIPT" "$@"
            ;;
    esac
}

# Run main function
main "$@"
