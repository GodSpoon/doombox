#!/bin/bash
# DoomBox Kiosk Startup Script
# This script prepares the environment and starts the kiosk application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Kiosk Starting..."
echo -e "==========================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo -e "${YELLOW}DoomBox directory: $SCRIPT_DIR${NC}"

# Create required directories
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/config"
mkdir -p "$SCRIPT_DIR/assets"

# Set up environment variables
export DISPLAY=:0
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

# Add /usr/games to PATH for doom executables
export PATH="/usr/games:$PATH"

# Function to check if process is running
check_process() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to wait for X11 to be ready
wait_for_x11() {
    echo -e "${YELLOW}Waiting for X11 to be ready...${NC}"
    local timeout=30
    while [ $timeout -gt 0 ]; do
        if xset q &>/dev/null; then
            echo -e "${GREEN}X11 is ready${NC}"
            return 0
        fi
        sleep 1
        ((timeout--))
    done
    echo -e "${RED}X11 not ready after 30 seconds, continuing anyway...${NC}"
    return 1
}

# Function to setup display
setup_display() {
    echo -e "${YELLOW}Setting up display...${NC}"
    
    # Disable screen blanking
    xset s off
    xset -dpms
    xset s noblank
    
    # Hide cursor
    unclutter -idle 1 -root &
    
    echo -e "${GREEN}Display setup complete${NC}"
}

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    MISSING_DEPS=""
    
    # Check Python dependencies
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv "$SCRIPT_DIR/venv"
    fi
    
    # Activate virtual environment
    source "$SCRIPT_DIR/venv/bin/activate"
    
    if ! python3 -c "import pygame, qrcode, sqlite3, cv2, numpy" 2>/dev/null; then
        echo -e "${RED}Missing Python dependencies. Installing...${NC}"
        pip install -r "$SCRIPT_DIR/requirements.txt"
    fi
    
    # Check system dependencies
    for cmd in "dsda-doom" "bluetoothctl" "unclutter"; do
        if ! command -v "$cmd" &> /dev/null; then
            MISSING_DEPS="$MISSING_DEPS $cmd"
        fi
    done
    
    # Check xset only if we have DISPLAY set
    if [ -n "$DISPLAY" ] && ! command -v "xset" &> /dev/null; then
        MISSING_DEPS="$MISSING_DEPS xset"
    fi
    
    if [ -n "$MISSING_DEPS" ]; then
        echo -e "${RED}Missing system dependencies:$MISSING_DEPS${NC}"
        echo -e "${YELLOW}Please install missing dependencies${NC}"
        return 1
    fi
    
    echo -e "${GREEN}All dependencies satisfied${NC}"
    return 0
}

# Function to setup controller
setup_controller() {
    echo -e "${YELLOW}Setting up controller...${NC}"
    
    # Enable Bluetooth
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
    
    # Setup controller auto-connect
    if [ -f "$SCRIPT_DIR/config/controller.json" ]; then
        echo -e "${GREEN}Controller config found, attempting auto-connect...${NC}"
        python3 "$SCRIPT_DIR/src/controller-input.py" --auto-connect --verbose
    else
        echo -e "${YELLOW}No controller config found. Controllers can be paired manually.${NC}"
    fi
}

# Function to start kiosk
start_kiosk() {
    echo -e "${YELLOW}Starting DoomBox kiosk...${NC}"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Start the kiosk application
    source "$SCRIPT_DIR/venv/bin/activate"
    python3 "$SCRIPT_DIR/src/kiosk-manager.py" 2>&1 | tee "$SCRIPT_DIR/logs/kiosk-startup.log"
}

# Main execution
main() {
    echo -e "${BLUE}DoomBox Kiosk Startup - $(date)${NC}"
    
    # Wait for X11 if we're in a graphical environment
    if [ -n "$DISPLAY" ]; then
        if wait_for_x11; then
            setup_display
        else
            echo -e "${YELLOW}Proceeding without X11 display setup${NC}"
        fi
    fi
    
    # Check dependencies
    if ! check_dependencies; then
        echo -e "${RED}Dependency check failed. Exiting.${NC}"
        exit 1
    fi
    
    # Setup controller
    setup_controller
    
    # Start kiosk
    start_kiosk
}

# Handle cleanup on exit
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    # Kill any background processes
    pkill -f unclutter 2>/dev/null || true
    echo -e "${GREEN}Cleanup complete${NC}"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Run main function
main "$@"
