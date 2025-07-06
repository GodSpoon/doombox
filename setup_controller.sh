#!/bin/bash

# DoomBox Controller Setup Integration
# Simple wrapper for the main setup.sh script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DoomBox Controller Setup${NC}"
echo -e "========================"
echo ""

# Check if scripts exist
if [ ! -f "$SCRIPT_DIR/pair_controller.sh" ]; then
    echo -e "${RED}❌ Controller scripts not found${NC}"
    echo -e "   Make sure you're running this from the correct directory"
    exit 1
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/pair_controller.sh"
chmod +x "$SCRIPT_DIR/debug_controller.sh"
chmod +x "$SCRIPT_DIR/auto_connect_controller.sh"

echo -e "${GREEN}✓ Controller scripts are ready${NC}"
echo ""
echo -e "${YELLOW}Available commands:${NC}"
echo -e "  ${BLUE}./pair_controller.sh${NC}         - Pair a new DualShock 4 controller"
echo -e "  ${BLUE}./debug_controller.sh${NC}        - Debug and test controller"
echo -e "  ${BLUE}./auto_connect_controller.sh${NC} - Auto-connect paired controller"
echo ""
echo -e "${YELLOW}Quick setup:${NC}"
echo -e "  1. Run: ${BLUE}./pair_controller.sh${NC}"
echo -e "  2. Follow the pairing instructions"
echo -e "  3. Test with: ${BLUE}./debug_controller.sh --status${NC}"
echo ""
echo -e "${CYAN}For detailed help, run any script with --help${NC}"
