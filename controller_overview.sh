#!/bin/bash

# DoomBox Controller System Summary
# Shows all available controller functionality

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo -e "  DoomBox Controller System"
echo -e "  Complete Setup & Management"
echo -e "==========================================${NC}"
echo ""

echo -e "${YELLOW}🎮 Controller Scripts Available:${NC}"
echo ""

# Check which scripts exist
SCRIPTS=(
    "pair_controller.sh:Main pairing script for DualShock 4"
    "debug_controller.sh:Debug and test controller functionality"
    "auto_connect_controller.sh:Auto-connect paired controllers"
    "setup_controller.sh:Setup helper and overview"
)

for script_info in "${SCRIPTS[@]}"; do
    IFS=':' read -r script desc <<< "$script_info"
    if [ -f "$script" ]; then
        echo -e "${GREEN}✓${NC} ${CYAN}$script${NC} - $desc"
    else
        echo -e "${RED}❌${NC} ${CYAN}$script${NC} - $desc (not found)"
    fi
done

echo ""
echo -e "${YELLOW}📖 Documentation:${NC}"
if [ -f "CONTROLLER_README.md" ]; then
    echo -e "${GREEN}✓${NC} ${CYAN}CONTROLLER_README.md${NC} - Complete documentation"
else
    echo -e "${RED}❌${NC} ${CYAN}CONTROLLER_README.md${NC} - Documentation (not found)"
fi

echo ""
echo -e "${YELLOW}🚀 Quick Start Guide:${NC}"
echo ""
echo -e "${BLUE}1. Setup Environment:${NC}"
echo -e "   • Make sure Bluetooth is working: ${CYAN}systemctl status bluetooth${NC}"
echo -e "   • Install dependencies: ${CYAN}sudo apt install bluetooth bluez bluez-tools joystick${NC}"
echo ""
echo -e "${BLUE}2. Pair Controller:${NC}"
echo -e "   • Turn OFF DualShock 4 controller"
echo -e "   • Run: ${CYAN}./pair_controller.sh${NC}"
echo -e "   • Follow pairing instructions"
echo ""
echo -e "${BLUE}3. Test Controller:${NC}"
echo -e "   • Quick status: ${CYAN}./debug_controller.sh --status${NC}"
echo -e "   • Full debug: ${CYAN}./debug_controller.sh${NC}"
echo -e "   • Test input: ${CYAN}./debug_controller.sh --test-input${NC}"
echo ""
echo -e "${BLUE}4. Integration:${NC}"
echo -e "   • Controller works with DoomBox kiosk automatically"
echo -e "   • Use Konami code: ${CYAN}↑↑↓↓←→←→BA${NC} for test games"
echo -e "   • Auto-reconnect: ${CYAN}./auto_connect_controller.sh${NC}"
echo ""

echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
echo ""
echo -e "${CYAN}Common Issues:${NC}"
echo -e "• ${YELLOW}Controller not found${NC}: Make sure it's in pairing mode (flashing white)"
echo -e "• ${YELLOW}Pairing fails${NC}: Try ${CYAN}./pair_controller.sh --force${NC}"
echo -e "• ${YELLOW}No joystick device${NC}: Check with ${CYAN}ls /dev/input/js*${NC}"
echo -e "• ${YELLOW}Bluetooth issues${NC}: ${CYAN}sudo systemctl restart bluetooth${NC}"
echo ""

echo -e "${YELLOW}💡 Advanced Usage:${NC}"
echo ""
echo -e "${CYAN}Script Options:${NC}"
echo -e "• ${CYAN}./pair_controller.sh --help${NC} - Show all pairing options"
echo -e "• ${CYAN}./debug_controller.sh --help${NC} - Show all debugging options"
echo -e "• ${CYAN}./pair_controller.sh --scan-only${NC} - Just scan for controllers"
echo -e "• ${CYAN}./debug_controller.sh --continuous${NC} - Monitor controller status"
echo ""

echo -e "${YELLOW}📋 System Requirements:${NC}"
echo ""
echo -e "${GREEN}Required:${NC}"
echo -e "• Bluetooth adapter (built-in or USB)"
echo -e "• DualShock 4 controller"
echo -e "• Linux with BlueZ stack"
echo ""
echo -e "${GREEN}Optional:${NC}"
echo -e "• pygame for Python testing"
echo -e "• jstest for input testing"
echo ""

echo -e "${YELLOW}🔗 Integration with DoomBox:${NC}"
echo ""
echo -e "• ${CYAN}Konami Code Detection${NC}: Main kiosk can detect controller input"
echo -e "• ${CYAN}Game Control${NC}: Controller works with DOOM and other games"
echo -e "• ${CYAN}Auto-reconnect${NC}: Controller reconnects automatically on boot"
echo -e "• ${CYAN}Status Display${NC}: Kiosk shows controller connection status"
echo ""

echo -e "${BLUE}=========================================="
echo -e "  Ready to Setup Your Controller!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "1. Run: ${CYAN}./pair_controller.sh${NC}"
echo -e "2. Test: ${CYAN}./debug_controller.sh --status${NC}"
echo -e "3. Play: Start the DoomBox kiosk!"
echo ""
echo -e "${YELLOW}For detailed help, run any script with ${CYAN}--help${NC}"
echo ""
