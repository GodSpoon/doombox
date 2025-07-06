#!/bin/bash
# Start minimal X server for DoomBox kiosk on physical display

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo -e "  DoomBox X Server Startup"
echo -e "==========================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Kill any existing X server on display :0
echo -e "${YELLOW}Cleaning up any existing X server...${NC}"
pkill -f "X :0" || true
pkill -f "Xorg :0" || true
sleep 2

# Start minimal X server on the physical display
echo -e "${YELLOW}Starting X server on physical display...${NC}"
X :0 -ac -nolisten tcp -dpi 96 &
X_PID=$!

# Wait for X server to be ready
echo -e "${YELLOW}Waiting for X server to initialize...${NC}"
sleep 5

# Set display environment
export DISPLAY=:0

# Test if X server is ready
if ! xset q &>/dev/null; then
    echo -e "${RED}X server failed to start properly${NC}"
    kill $X_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}X server is ready on display :0${NC}"

# Configure X server for kiosk
echo -e "${YELLOW}Configuring X server for kiosk mode...${NC}"
xset s off          # Disable screen saver
xset -dpms          # Disable power management
xset s noblank      # Disable screen blanking
xrandr --output HDMI-1 --mode 1280x960 --rate 60 2>/dev/null || true

# Hide cursor
unclutter -idle 1 -root &

# Set black background
xsetroot -solid black

echo -e "${GREEN}X server configured for kiosk mode${NC}"

# Start the kiosk application
echo -e "${YELLOW}Starting DoomBox kiosk application...${NC}"
cd "$SCRIPT_DIR"
exec ./start-kiosk.sh

# Cleanup function (won't reach here due to exec, but good practice)
cleanup() {
    echo -e "${YELLOW}Shutting down X server...${NC}"
    pkill -f unclutter 2>/dev/null || true
    kill $X_PID 2>/dev/null || true
}

trap cleanup EXIT INT TERM
