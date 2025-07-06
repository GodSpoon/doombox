#!/bin/bash
# DoomBox Controller Management Script
# Consolidated controller pairing, debugging, and management

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROLLER_SCRIPT="$SCRIPT_DIR/../src/controller-input.py"

show_help() {
    echo "DoomBox Controller Management"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  scan                Scan for controllers"
    echo "  pair MAC_ADDR       Pair with specific controller"
    echo "  connect MAC_ADDR    Connect to specific controller"
    echo "  auto-connect        Auto-connect to saved controller"
    echo "  status              Show controller status"
    echo "  test                Test controller input"
    echo "  setup               Setup Bluetooth and dependencies"
    echo ""
    echo "Options:"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -h, --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 scan                     # Scan for controllers"
    echo "  $0 pair 20:50:E7:D2:6F:E3   # Pair specific controller"
    echo "  $0 auto-connect             # Connect to saved controller"
    echo "  $0 status                   # Show status"
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python script exists
    if [ ! -f "$CONTROLLER_SCRIPT" ]; then
        echo -e "${RED}❌ Controller script not found: $CONTROLLER_SCRIPT${NC}"
        return 1
    fi
    
    # Check Python 3
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        return 1
    fi
    
    # Check required system tools
    local missing_deps=()
    for cmd in bluetoothctl hciconfig rfkill systemctl; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Install with: sudo apt install bluetooth bluez bluez-tools rfkill${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ All dependencies found${NC}"
    return 0
}

setup_system() {
    echo -e "${YELLOW}Setting up system for controller support...${NC}"
    
    # Update packages
    sudo apt update
    
    # Install required packages
    sudo apt install -y bluetooth bluez bluez-tools rfkill joystick jstest-gtk python3
    
    # Enable and start services
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
    
    # Unblock Bluetooth
    sudo rfkill unblock bluetooth
    
    # Power on adapter
    sudo hciconfig hci0 up 2>/dev/null || true
    
    echo -e "${GREEN}✓ System setup completed${NC}"
}

run_controller_command() {
    local cmd="$1"
    shift
    
    local verbose_flag=""
    if [ "$VERBOSE" = "true" ]; then
        verbose_flag="--verbose"
    fi
    
    python3 "$CONTROLLER_SCRIPT" "$verbose_flag" "$cmd" "$@"
}

# Parse command line arguments
VERBOSE=false
COMMAND=""
ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        scan|pair|connect|auto-connect|status|test|setup)
            COMMAND="$1"
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Main execution
main() {
    if [ -z "$COMMAND" ]; then
        show_help
        exit 1
    fi
    
    case "$COMMAND" in
        setup)
            setup_system
            ;;
        scan)
            if check_dependencies; then
                run_controller_command "--scan"
            fi
            ;;
        pair)
            if [ ${#ARGS[@]} -eq 0 ]; then
                echo -e "${RED}❌ MAC address required for pairing${NC}"
                exit 1
            fi
            if check_dependencies; then
                run_controller_command "--pair" "${ARGS[0]}"
            fi
            ;;
        connect)
            if [ ${#ARGS[@]} -eq 0 ]; then
                echo -e "${RED}❌ MAC address required for connection${NC}"
                exit 1
            fi
            if check_dependencies; then
                run_controller_command "--connect" "${ARGS[0]}"
            fi
            ;;
        auto-connect)
            if check_dependencies; then
                run_controller_command "--auto-connect"
            fi
            ;;
        status)
            if check_dependencies; then
                run_controller_command "--status"
            fi
            ;;
        test)
            if check_dependencies; then
                run_controller_command "--test"
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
