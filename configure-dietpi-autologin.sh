#!/bin/bash
# DietPi Autologin Configuration Script for DoomBox
# This script configures DietPi to automatically login and start the kiosk

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo -e "  DoomBox DietPi Autologin Setup"
echo -e "==========================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
DOOMBOX_DIR="$SCRIPT_DIR"

# Check if running on DietPi
if [ ! -f "/boot/dietpi/.dietpi_hw_model" ]; then
    echo -e "${RED}This script is designed for DietPi systems only.${NC}"
    echo -e "${YELLOW}Please run this on a DietPi system.${NC}"
    exit 1
fi

# Function to configure DietPi autologin
configure_dietpi_autologin() {
    echo -e "${YELLOW}Configuring DietPi autologin...${NC}"
    
    # Backup original dietpi.txt
    sudo cp /boot/dietpi.txt /boot/dietpi.txt.backup
    
    # Configure autologin settings in dietpi.txt
    cat << EOF | sudo tee -a /boot/dietpi.txt

# DoomBox Kiosk Configuration
AUTO_SETUP_AUTOSTART_TARGET_INDEX=7
AUTO_SETUP_AUTOSTART_LOGIN_USER=dietpi
AUTO_SETUP_CUSTOM_SCRIPT_EXEC=1
EOF
    
    echo -e "${GREEN}DietPi autologin configured${NC}"
}

# Function to create custom startup script for DietPi
create_dietpi_startup() {
    echo -e "${YELLOW}Creating DietPi custom startup script...${NC}"
    
    # Create the custom script that DietPi will run
    cat << EOF | sudo tee /boot/Automation_Custom_Script.sh
#!/bin/bash
# DoomBox DietPi Autologin Script
# This script is executed by DietPi automation system

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\${GREEN}DoomBox: Starting kiosk setup...\${NC}"

# Install required packages
echo -e "\${YELLOW}Installing system dependencies...\${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-opencv libopencv-dev \\
    ffmpeg libavcodec-dev libavformat-dev libswscale-dev \\
    dsda-doom doom-wad-shareware sqlite3 bluetooth bluez bluez-tools \\
    joystick jstest-gtk feh unclutter xset

# Install Python dependencies
echo -e "\${YELLOW}Installing Python dependencies...\${NC}"
pip3 install -r $DOOMBOX_DIR/requirements.txt

# Create systemd service
echo -e "\${YELLOW}Creating systemd service...\${NC}"
cp $DOOMBOX_DIR/doombox-kiosk.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable doombox-kiosk.service

# Configure dsda-doom
echo -e "\${YELLOW}Configuring dsda-doom...\${NC}"
mkdir -p /root/.dsda-doom
cat << DOOM_EOF > /root/.dsda-doom/dsda-doom.cfg
# DoomBox dsda-doom configuration
use_joystick 1
joy_left 0
joy_right 1
joy_up 2
joy_down 3
joy_fire 4
joy_use 5
joy_run 6
joy_strafe 7
joy_menu 8
joy_weapon_next 9
joy_weapon_prev 10
DOOM_EOF

# Configure X11 autologin
echo -e "\${YELLOW}Configuring X11 autologin...\${NC}"
systemctl set-default graphical.target

# Start kiosk service
echo -e "\${YELLOW}Starting DoomBox kiosk service...\${NC}"
systemctl start doombox-kiosk.service

echo -e "\${GREEN}DoomBox setup complete!${NC}"
EOF

    # Make the script executable
    sudo chmod +x /boot/Automation_Custom_Script.sh
    
    echo -e "${GREEN}Custom startup script created${NC}"
}

# Function to configure systemd service
configure_systemd_service() {
    echo -e "${YELLOW}Configuring systemd service...${NC}"
    
    # Update the service file with correct paths
    cat << EOF | sudo tee /etc/systemd/system/doombox-kiosk.service
[Unit]
Description=DoomBox Kiosk Application
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=dietpi
Group=dietpi
WorkingDirectory=$DOOMBOX_DIR
Environment=DISPLAY=:0
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
ExecStartPre=/bin/sleep 10
ExecStart=$DOOMBOX_DIR/start-kiosk.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable doombox-kiosk.service
    
    echo -e "${GREEN}Systemd service configured${NC}"
}

# Function to configure local autologin (alternative method)
configure_local_autologin() {
    echo -e "${YELLOW}Configuring local autologin method...${NC}"
    
    # Create user's .bashrc modification
    cat << EOF >> ~/.bashrc

# DoomBox Kiosk Auto-start
if [ -z "\$SSH_CONNECTION" ] && [ \$(tty) = "/dev/tty1" ]; then
    # Start X11 if not already running
    if [ -z "\$DISPLAY" ]; then
        startx
    fi
fi
EOF
    
    # Create .xinitrc for X11 startup
    cat << EOF > ~/.xinitrc
#!/bin/bash
# DoomBox X11 startup script

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 1 -root &

# Start DoomBox kiosk
cd $DOOMBOX_DIR
exec $DOOMBOX_DIR/start-kiosk.sh
EOF
    
    chmod +x ~/.xinitrc
    
    echo -e "${GREEN}Local autologin configured${NC}"
}

# Function to show configuration summary
show_summary() {
    echo -e "${BLUE}=========================================="
    echo -e "  Configuration Summary"
    echo -e "==========================================${NC}"
    echo -e "${GREEN}✓ DietPi autologin configured${NC}"
    echo -e "${GREEN}✓ Custom startup script created${NC}"
    echo -e "${GREEN}✓ Systemd service configured${NC}"
    echo -e "${GREEN}✓ Local autologin backup configured${NC}"
    echo -e ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. Reboot the system to test autologin"
    echo -e "2. The kiosk should start automatically"
    echo -e "3. Check logs: journalctl -u doombox-kiosk.service"
    echo -e "4. Check kiosk logs: $DOOMBOX_DIR/logs/"
    echo -e ""
    echo -e "${YELLOW}Manual control:${NC}"
    echo -e "Start:   sudo systemctl start doombox-kiosk.service"
    echo -e "Stop:    sudo systemctl stop doombox-kiosk.service"
    echo -e "Status:  sudo systemctl status doombox-kiosk.service"
    echo -e "Logs:    journalctl -u doombox-kiosk.service -f"
}

# Main execution
main() {
    echo -e "${BLUE}DoomBox DietPi Autologin Setup - $(date)${NC}"
    
    # Check if running as root for some operations
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}Some operations require root privileges.${NC}"
        echo -e "${YELLOW}Please run with sudo or as root.${NC}"
    fi
    
    # Configure DietPi autologin
    configure_dietpi_autologin
    
    # Create DietPi startup script
    create_dietpi_startup
    
    # Configure systemd service
    configure_systemd_service
    
    # Configure local autologin as backup
    configure_local_autologin
    
    # Show summary
    show_summary
    
    echo -e "${GREEN}DoomBox autologin setup complete!${NC}"
    echo -e "${YELLOW}Please reboot to test the configuration.${NC}"
}

# Handle cleanup on exit
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Run main function
main "$@"
