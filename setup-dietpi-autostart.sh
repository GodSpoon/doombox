#!/bin/bash
# DoomBox DietPi AutoStart Setup Script
# Run this script on the DietPi system to configure autologin

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo -e "  DoomBox DietPi AutoStart Setup"
echo -e "==========================================${NC}"

# Check if running on DietPi
if [ ! -f "/boot/dietpi/.dietpi_hw_model" ]; then
    echo -e "${RED}This script must be run on a DietPi system${NC}"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo -e "${YELLOW}Please run: sudo $0${NC}"
    exit 1
fi

# Check if doombox directory exists
if [ ! -d "/root/doombox" ]; then
    echo -e "${RED}DoomBox directory not found at /root/doombox${NC}"
    echo -e "${YELLOW}Please clone the repository first:${NC}"
    echo -e "  git clone <repository-url> /root/doombox"
    exit 1
fi

echo -e "${YELLOW}Setting up DietPi AutoStart for DoomBox...${NC}"

# Copy custom script to DietPi AutoStart location
echo -e "${YELLOW}Installing custom AutoStart script...${NC}"
cp /root/doombox/dietpi-custom-script.sh /var/lib/dietpi/dietpi-autostart/custom.sh
chmod +x /var/lib/dietpi/dietpi-autostart/custom.sh

# Configure DietPi to use custom AutoStart (index 7)
echo -e "${YELLOW}Configuring DietPi AutoStart...${NC}"
dietpi-autostart 7

# Make sure start-kiosk.sh is executable
chmod +x /root/doombox/start-kiosk.sh

# Create log directory
mkdir -p /var/log
touch /var/log/doombox-autostart.log

echo -e "${GREEN}✓ DietPi AutoStart configured successfully!${NC}"
echo -e ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo -e "• AutoStart mode: Custom (index 7)"
echo -e "• Script location: /var/lib/dietpi/dietpi-autostart/custom.sh"
echo -e "• DoomBox directory: /root/doombox"
echo -e "• Log file: /var/log/doombox-autostart.log"
echo -e ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Reboot the system to test autologin"
echo -e "2. The DoomBox kiosk should start automatically"
echo -e "3. Check logs if needed:"
echo -e "   • AutoStart log: tail -f /var/log/doombox-autostart.log"
echo -e "   • Kiosk log: tail -f /root/doombox/logs/kiosk.log"
echo -e ""
echo -e "${GREEN}Ready to reboot and test!${NC}"
