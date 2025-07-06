#!/bin/bash

# DoomBox Uninstall Script
# Provides options to remove DoomBox files and/or system packages

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo bash uninstall.sh)${NC}"
    exit 1
fi

echo -e "${RED}=========================================="
echo -e "  DoomBox Uninstall Script"
echo -e "  ⚠️  DESTRUCTIVE OPERATION ⚠️"
echo -e "==========================================${NC}"
echo ""

# Define what will be removed in each option
show_removal_details() {
    local option=$1
    
    case $option in
        1)
            echo -e "${YELLOW}Option 1 - Remove DoomBox Files Only:${NC}"
            echo "✓ Stop and disable DoomBox service"
            echo "✓ Remove /opt/doombox/ directory and all contents"
            echo "✓ Remove DoomBox desktop entries from XFCE menu"
            echo "✓ Remove systemd service files"
            echo "✓ Remove auto-login configuration"
            echo "✓ Remove lzdoom compatibility wrapper"
            echo ""
            echo -e "${GREEN}Will NOT remove:${NC}"
            echo "• System packages (Python, DOOM engine, etc.)"
            echo "• User data outside /opt/doombox/"
            echo "• System-wide configurations"
            ;;
        2)
            echo -e "${YELLOW}Option 2 - Complete Removal (Files + Packages):${NC}"
            echo "✓ Everything from Option 1, PLUS:"
            echo "✓ Remove DoomBox-related packages:"
            echo "  - dsda-doom (DOOM engine)"
            echo "  - mosquitto (MQTT broker)"
            echo "  - Python packages (pygame, qrcode, etc.)"
            echo "  - Bluetooth packages (bluez, bluez-tools)"
            echo "  - Development tools (if installed by setup)"
            echo ""
            echo -e "${RED}⚠️  WARNING: This may affect other applications!${NC}"
            ;;
        3)
            echo -e "${YELLOW}Option 3 - Nuclear Option (Everything):${NC}"
            echo "✓ Everything from Option 2, PLUS:"
            echo "✓ Remove ALL packages installed by setup script:"
            echo "  - XFCE desktop environment"
            echo "  - X11 server components"
            echo "  - Development libraries"
            echo "  - System utilities"
            echo ""
            echo -e "${RED}⚠️  EXTREME WARNING: This will remove desktop environment!${NC}"
            echo -e "${RED}⚠️  System may become unusable for GUI applications!${NC}"
            ;;
    esac
    echo ""
}

# Show menu and get user choice
show_menu() {
    echo -e "${BLUE}Choose removal option:${NC}"
    echo ""
    echo "1) Remove DoomBox Files Only (Recommended)"
    echo "2) Remove DoomBox Files + Related Packages"  
    echo "3) Nuclear Option - Remove Everything"
    echo "4) Show detailed removal lists"
    echo "5) Cancel and exit"
    echo ""
    echo -n "Enter your choice (1-5): "
}

# Get confirmation
confirm_removal() {
    local option=$1
    echo ""
    echo -e "${RED}Are you absolutely sure you want to proceed?${NC}"
    echo -e "${RED}This action cannot be undone!${NC}"
    echo ""
    echo -n "Type 'YES' (all caps) to confirm: "
    read confirmation
    
    if [ "$confirmation" != "YES" ]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 0
    fi
}

# Stop and disable services
stop_services() {
    echo -e "${YELLOW}Stopping DoomBox services...${NC}"
    
    # Stop DoomBox service
    if systemctl is-active --quiet doombox 2>/dev/null; then
        systemctl stop doombox
        echo "✓ Stopped doombox service"
    fi
    
    if systemctl is-enabled --quiet doombox 2>/dev/null; then
        systemctl disable doombox
        echo "✓ Disabled doombox service"
    fi
    
    # Kill any running processes
    pkill -f "python.*kiosk.py" 2>/dev/null || true
    pkill -f "lzdoom" 2>/dev/null || true
    pkill -f "dsda-doom" 2>/dev/null || true
    
    echo "✓ Stopped all DoomBox processes"
}

# Remove DoomBox files
remove_doombox_files() {
    echo -e "${YELLOW}Removing DoomBox files...${NC}"
    
    # Remove main directory
    if [ -d "/opt/doombox" ]; then
        rm -rf /opt/doombox
        echo "✓ Removed /opt/doombox directory"
    fi
    
    # Remove systemd service
    if [ -f "/etc/systemd/system/doombox.service" ]; then
        rm -f /etc/systemd/system/doombox.service
        echo "✓ Removed systemd service file"
    fi
    
    # Remove lzdoom wrapper
    if [ -f "/usr/local/bin/lzdoom" ]; then
        rm -f /usr/local/bin/lzdoom
        echo "✓ Removed lzdoom compatibility wrapper"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    echo "✓ Reloaded systemd configuration"
}

# Remove desktop entries
remove_desktop_entries() {
    echo -e "${YELLOW}Removing desktop entries...${NC}"
    
    # List of DoomBox desktop entries
    local desktop_entries=(
        "doombox-kiosk.desktop"
        "doombox-test-doom.desktop"
        "doombox-test-dsda.desktop"
        "doombox-debug-controller.desktop"
        "doombox-pair-controller.desktop"
        "doombox-view-logs.desktop"
        "doombox-start-service.desktop"
        "doombox-stop-service.desktop"
        "doombox-view-scores.desktop"
        "doombox-start-x.desktop"
    )
    
    for entry in "${desktop_entries[@]}"; do
        if [ -f "/usr/share/applications/$entry" ]; then
            rm -f "/usr/share/applications/$entry"
            echo "✓ Removed $entry"
        fi
    done
    
    # Remove DoomBox directory entry
    if [ -f "/usr/share/desktop-directories/DoomBox.directory" ]; then
        rm -f /usr/share/desktop-directories/DoomBox.directory
        echo "✓ Removed DoomBox menu category"
    fi
    
    # Remove custom menu configuration
    if [ -f "/etc/xdg/menus/applications-doombox.menu" ]; then
        rm -f /etc/xdg/menus/applications-doombox.menu
        echo "✓ Removed custom menu configuration"
    fi
    
    # Remove autostart entry
    if [ -f "/etc/xdg/autostart/doombox-kiosk.desktop" ]; then
        rm -f /etc/xdg/autostart/doombox-kiosk.desktop
        echo "✓ Removed autostart entry"
    fi
    
    # Update desktop database
    update-desktop-database /usr/share/applications 2>/dev/null || true
    echo "✓ Updated desktop database"
}

# Remove auto-login configuration
remove_auto_login() {
    echo -e "${YELLOW}Removing auto-login configuration...${NC}"
    
    # Remove auto-login override
    if [ -d "/etc/systemd/system/getty@tty1.service.d" ]; then
        rm -rf /etc/systemd/system/getty@tty1.service.d
        echo "✓ Removed auto-login configuration"
        systemctl daemon-reload
    fi
    
    # Reset to default target if changed
    current_target=$(systemctl get-default)
    if [ "$current_target" = "multi-user.target" ]; then
        echo -n "Reset to graphical target? (y/N): "
        read reset_target
        if [[ $reset_target =~ ^[Yy] ]]; then
            systemctl set-default graphical.target
            echo "✓ Reset default target to graphical.target"
        fi
    fi
}

# Remove DoomBox-related packages
remove_doombox_packages() {
    echo -e "${YELLOW}Removing DoomBox-related packages...${NC}"
    
    local packages_to_remove=(
        "dsda-doom"
        "doom-wad-shareware"
        "mosquitto"
        "mosquitto-clients"
        "joystick"
        "jstest-gtk"
        "bluetooth"
        "bluez"
        "bluez-tools"
    )
    
    for package in "${packages_to_remove[@]}"; do
        if dpkg -l | grep -q "^ii.*$package "; then
            apt remove -y "$package"
            echo "✓ Removed $package"
        fi
    done
    
    # Remove Python packages from system if they were installed by pip
    echo "✓ Python packages were installed in virtual environment (already removed)"
}

# Remove all packages installed by setup
remove_all_packages() {
    echo -e "${YELLOW}Removing ALL packages installed by setup script...${NC}"
    echo -e "${RED}⚠️  This is the nuclear option!${NC}"
    
    local all_packages=(
        "git"
        "wget"
        "curl"
        "unzip"
        "bluetooth"
        "bluez"
        "bluez-tools"
        "joystick"
        "jstest-gtk"
        "feh"
        "mosquitto"
        "mosquitto-clients"
        "sqlite3"
        "dsda-doom"
        "doom-wad-shareware"
        "python3-pip"
        "python3-venv"
        "build-essential"
        "xorg"
        "xinit"
        "xfce4"
        "xfce4-goodies"
        "cmake"
        "libsdl2-dev"
        "libsdl2-mixer-dev"
        "libsdl2-image-dev"
        "libsdl2-net-dev"
    )
    
    echo -e "${RED}Packages to be removed:${NC}"
    printf '%s\n' "${all_packages[@]}" | column -c 80
    echo ""
    echo -e "${RED}⚠️  Your desktop environment will be removed!${NC}"
    echo -n "Continue? Type 'NUCLEAR' to proceed: "
    read nuclear_confirm
    
    if [ "$nuclear_confirm" != "NUCLEAR" ]; then
        echo -e "${YELLOW}Nuclear option cancelled.${NC}"
        return
    fi
    
    for package in "${all_packages[@]}"; do
        if dpkg -l | grep -q "^ii.*$package "; then
            apt remove -y "$package" 2>/dev/null || true
            echo "✓ Removed $package"
        fi
    done
    
    # Clean up
    apt autoremove -y
    apt autoclean
    echo "✓ Cleaned up package cache"
}

# Main removal function
perform_removal() {
    local option=$1
    
    echo -e "${GREEN}Starting removal process...${NC}"
    echo ""
    
    # Always perform these steps
    stop_services
    remove_doombox_files
    remove_desktop_entries
    remove_auto_login
    
    case $option in
        1)
            echo -e "${GREEN}✓ DoomBox files removed successfully!${NC}"
            ;;
        2)
            remove_doombox_packages
            echo -e "${GREEN}✓ DoomBox files and related packages removed!${NC}"
            ;;
        3)
            remove_doombox_packages
            remove_all_packages
            echo -e "${GREEN}✓ Complete nuclear removal finished!${NC}"
            echo -e "${YELLOW}⚠️  You may need to reinstall desktop environment!${NC}"
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "  Removal Complete!"
    echo -e "==========================================${NC}"
    echo ""
    echo "What was removed:"
    echo "• DoomBox service and files"
    echo "• Desktop menu entries"
    echo "• System configurations"
    
    if [ $option -ge 2 ]; then
        echo "• DoomBox-related packages"
    fi
    
    if [ $option -eq 3 ]; then
        echo "• Desktop environment and X11"
        echo ""
        echo -e "${YELLOW}To restore desktop environment:${NC}"
        echo "  sudo apt update"
        echo "  sudo apt install xfce4 lightdm"
        echo "  sudo systemctl enable lightdm"
    fi
    
    echo ""
    echo "Consider rebooting to ensure all changes take effect."
}

# Main script execution
main() {
    while true; do
        show_menu
        read choice
        
        case $choice in
            1|2|3)
                echo ""
                show_removal_details $choice
                confirm_removal $choice
                perform_removal $choice
                break
                ;;
            4)
                echo ""
                show_removal_details 1
                show_removal_details 2  
                show_removal_details 3
                echo -n "Press Enter to return to menu..."
                read
                echo ""
                ;;
            5)
                echo -e "${YELLOW}Uninstall cancelled.${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1-5.${NC}"
                echo ""
                ;;
        esac
    done
}

# Run main function
main
