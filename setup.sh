#!/bin/bash

# shmegl's DoomBox Setup Script
# Builds the DoomBox application in a local "app" folder
# Run from the repository root: bash setup.sh

set -e

echo "=========================================="
echo "  Shmegl's DoomBox Setup"
echo "  made 4 hot ppl"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located (should be repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo -e "${YELLOW}Running from: $SCRIPT_DIR${NC}"

# Define paths - everything goes in the "app" folder
DOOMBOX_DIR="$SCRIPT_DIR/app"
DOOM_DIR="$DOOMBOX_DIR/doom"
LOGS_DIR="$DOOMBOX_DIR/logs"
FONTS_DIR="$DOOMBOX_DIR/fonts"

echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$DOOMBOX_DIR"
mkdir -p "$DOOM_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$FONTS_DIR"

echo -e "${YELLOW}System dependencies required:${NC}"
echo -e "${BLUE}Please ensure the following packages are installed:${NC}"
echo -e "  - git, wget, curl, unzip"
echo -e "  - python3, python3-pip, python3-venv"
echo -e "  - python3-opencv, libopencv-dev"
echo -e "  - ffmpeg, libavcodec-dev, libavformat-dev, libswscale-dev"
echo -e "  - dsda-doom, doom-wad-shareware"
echo -e "  - sqlite3"
echo -e "  - bluetooth, bluez, bluez-tools, joystick, jstest-gtk"
echo -e "  - feh, mosquitto, mosquitto-clients (optional)"
echo -e ""
echo -e "${YELLOW}To install on Debian/Ubuntu:${NC}"
echo -e "sudo apt update && sudo apt install -y git wget curl unzip python3 python3-pip python3-venv python3-opencv libopencv-dev ffmpeg libavcodec-dev libavformat-dev libswscale-dev dsda-doom doom-wad-shareware sqlite3 bluetooth bluez bluez-tools joystick jstest-gtk feh mosquitto mosquitto-clients"
echo -e ""

# Check for critical dependencies
MISSING_DEPS=()
command -v python3 >/dev/null || MISSING_DEPS+=("python3")
command -v pip3 >/dev/null || command -v python3 -m pip >/dev/null || MISSING_DEPS+=("python3-pip")
command -v dsda-doom >/dev/null || [ -f "/usr/games/dsda-doom" ] || MISSING_DEPS+=("dsda-doom")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}Missing critical dependencies: ${MISSING_DEPS[*]}${NC}"
    echo -e "${YELLOW}Please install them before continuing.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Critical dependencies found${NC}"

echo -e "${YELLOW}Setting up DOOM engine (dsda-doom)...${NC}"
# Check for dsda-doom installation
if command -v dsda-doom &>/dev/null; then
    DOOM_ENGINE="dsda-doom"
    echo "Found dsda-doom engine"
elif [ -f "/usr/games/dsda-doom" ]; then
    DOOM_ENGINE="/usr/games/dsda-doom"
    echo "Found dsda-doom in /usr/games/"
else
    echo -e "${RED}dsda-doom not found!${NC}"
    echo -e "${YELLOW}Please install dsda-doom:${NC}"
    echo -e "  sudo apt install dsda-doom"
    exit 1
fi

echo "Using DOOM engine: $DOOM_ENGINE"

# Create lzdoom compatibility wrapper script
echo "Creating lzdoom compatibility wrapper for dsda-doom..."
cat >"$DOOMBOX_DIR/lzdoom" <<'EOF'
#!/bin/bash
# DOOM engine wrapper script for DoomBox compatibility
# Translates lzdoom/gzdoom arguments to dsda-doom compatible format

DOOM_ARGS=()
IWAD_PATH=""
PLAYER_NAME=""
WIDTH="640"
HEIGHT="480"
FULLSCREEN=false

# Parse arguments to convert lzdoom/gzdoom style to dsda-doom
while [[ $# -gt 0 ]]; do
    case $1 in
        -iwad)
            IWAD_PATH="$2"
            shift 2
            ;;
        -width)
            WIDTH="$2"
            shift 2
            ;;
        -height)
            HEIGHT="$2"
            shift 2
            ;;
        -fullscreen)
            FULLSCREEN=true
            shift
            ;;
        +name)
            PLAYER_NAME="$2"
            shift 2
            ;;
        *)
            # Pass through other arguments
            DOOM_ARGS+=("$1")
            shift
            ;;
    esac
done

# Build dsda-doom command
DOOM_CMD=(dsda-doom)

if [ -n "$IWAD_PATH" ]; then
    DOOM_CMD+=(-iwad "$IWAD_PATH")
fi

# Set video mode for dsda-doom
DOOM_CMD+=(-width "$WIDTH" -height "$HEIGHT")

# Set fullscreen mode
if [ "$FULLSCREEN" = true ]; then
    DOOM_CMD+=(-fullscreen)
fi

# Player name handling for dsda-doom
if [ -n "$PLAYER_NAME" ]; then
    # dsda-doom uses different syntax for player names
    DOOM_CMD+=(-playername "$PLAYER_NAME")
fi

# Add any additional arguments
DOOM_CMD+=("${DOOM_ARGS[@]}")

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$0")/logs"

# Log the command for debugging
echo "$(date): DOOM Command: ${DOOM_CMD[*]}" >> "$(dirname "$0")/logs/doom.log"

# Execute dsda-doom
exec "${DOOM_CMD[@]}"
EOF

chmod +x "$DOOMBOX_DIR/lzdoom"
echo -e "${GREEN}lzdoom compatibility wrapper created!${NC}"

echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
cd "$DOOMBOX_DIR"

# Create virtual environment only if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating new virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}Virtual environment already exists${NC}"
fi

source venv/bin/activate

# Check if packages are already installed
PACKAGES_INSTALLED=false
if python3 -c "import pygame, cv2, numpy, paho.mqtt, requests" 2>/dev/null; then
    PACKAGES_INSTALLED=true
    echo -e "${GREEN}Python packages already installed${NC}"
fi

if [ "$PACKAGES_INSTALLED" = false ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install --upgrade pip

    # Force reinstall of NumPy and OpenCV to ensure compatibility
    echo -e "${YELLOW}Ensuring NumPy 1.x compatibility...${NC}"
    pip uninstall -y numpy opencv-python 2>/dev/null || true
    pip install "numpy<2.0.0"

    # Check if requirements.txt exists in the repo
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo -e "${YELLOW}Installing from requirements.txt...${NC}"
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        echo -e "${YELLOW}Installing default Python packages...${NC}"
        # Install NumPy 1.x first to avoid compatibility issues with OpenCV
        pip install "numpy<2.0.0"
        pip install pygame opencv-python paho-mqtt requests
    fi
else
    echo -e "${YELLOW}Checking NumPy compatibility...${NC}"
    NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "unknown")
    if [[ "$NUMPY_VERSION" == "2."* ]]; then
        echo -e "${YELLOW}NumPy 2.x detected, downgrading for OpenCV compatibility...${NC}"
        pip uninstall -y numpy opencv-python 2>/dev/null || true
        pip install "numpy<2.0.0"
        pip install opencv-python==4.8.1.78
    else
        echo -e "${GREEN}NumPy version $NUMPY_VERSION is compatible${NC}"
    fi
fi

echo -e "${YELLOW}Downloading DOOM.WAD...${NC}"
cd "$DOOM_DIR"
if [ ! -f "DOOM.WAD" ]; then
    wget -O "DOOM.WAD" "https://archive.org/download/theultimatedoom_doom2_doom.wad/DOOM.WAD%20%28For%20GZDoom%29/DOOM.WAD"
    echo -e "${GREEN}DOOM.WAD downloaded successfully${NC}"
else
    echo -e "${GREEN}DOOM.WAD already exists${NC}"
fi

echo -e "${YELLOW}Copying application files from repository...${NC}"
cd "$DOOMBOX_DIR"

# Copy main application files
if [ -f "$SCRIPT_DIR/kiosk.py" ]; then
    echo "Copying kiosk.py..."
    cp "$SCRIPT_DIR/kiosk.py" ./
else
    echo -e "${RED}kiosk.py not found in repository!${NC}"
    exit 1
fi

[ -f "$SCRIPT_DIR/config.py" ] && cp "$SCRIPT_DIR/config.py" ./
[ -f "$SCRIPT_DIR/webhook.py" ] && cp "$SCRIPT_DIR/webhook.py" ./

# Copy controller scripts from repository
echo -e "${YELLOW}Setting up controller scripts...${NC}"

# List of controller scripts to copy
CONTROLLER_SCRIPTS=(
    "pair_controller.sh"
    "debug_controller.sh"  
    "auto_connect_controller.sh"
    "setup_controller.sh"
    "CONTROLLER_README.md"
)

# Copy controller scripts if they exist in the repo
for script in "${CONTROLLER_SCRIPTS[@]}"; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        echo "Copying $script..."
        cp "$SCRIPT_DIR/$script" "$DOOMBOX_DIR/"
        chmod +x "$DOOMBOX_DIR/$script" 2>/dev/null || true
    else
        echo "⚠️  $script not found in repository"
    fi
done

echo -e "${GREEN}✓ Controller scripts copied${NC}"

# Copy web form files if they exist
if [ -d "$SCRIPT_DIR/form" ]; then
    cp -r "$SCRIPT_DIR/form" ./
elif [ -f "$SCRIPT_DIR/index.html" ]; then
    mkdir -p form
    cp "$SCRIPT_DIR/index.html" ./form/
    [ -f "$SCRIPT_DIR/CNAME" ] && cp "$SCRIPT_DIR/CNAME" ./form/
fi

# Copy fonts
if [ -d "$SCRIPT_DIR/fonts" ]; then
    echo -e "${YELLOW}Copying fonts...${NC}"
    cp -r "$SCRIPT_DIR/fonts"/* "$FONTS_DIR/"
    echo -e "${GREEN}✅ Fonts copied:${NC}"
    ls -la "$FONTS_DIR/" | grep -E "\.(ttf|otf)$" | wc -l | xargs echo "   Font files:"
else
    echo -e "${YELLOW}⚠️  No fonts directory found in repo${NC}"
fi

# Note: Videos and images are used directly from git repo - no copying needed
echo -e "${GREEN}✅ Using media files directly from git repository${NC}"

echo -e "${GREEN}Repository files copied successfully!${NC}" echo -e "${YELLOW}Creating startup scripts...${NC}"
cat >"$DOOMBOX_DIR/start.sh" <<'EOF'
#!/bin/bash
# DoomBox Kiosk Startup Script

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

# Activate Python virtual environment
source venv/bin/activate

# Set display if not set
export DISPLAY=${DISPLAY:-:0}

# Start the kiosk application
echo "Starting DoomBox Kiosk..."
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/start.sh"

cat >"$DOOMBOX_DIR/start_with_x.sh" <<'EOF'
#!/bin/bash
# Start X server and DoomBox kiosk

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

export DISPLAY=:0

# Start X server in background if not running
if ! xset q &>/dev/null; then
    echo "Starting X server..."
    startx &
    sleep 5

    # Wait for X to be ready
    timeout=30
    while [ $timeout -gt 0 ]; do
        if xset q &>/dev/null; then
            echo "X server ready"
            break
        fi
        echo "Waiting for X server... ($timeout)"
        sleep 1
        ((timeout--))
    done
fi

# Hide cursor and disable screen blanking
xset s off
xset -dpms
xset s noblank
unclutter -idle 1 -root &>/dev/null &

# Start the kiosk
./start.sh
EOF

chmod +x "$DOOMBOX_DIR/start_with_x.sh"

# Helper scripts for testing
cat >"$DOOMBOX_DIR/test_kiosk.sh" <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
export DISPLAY=${DISPLAY:-:0}
echo "Testing DoomBox Kiosk..."
python kiosk.py
EOF

cat >"$DOOMBOX_DIR/test_dsda_doom.sh" <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo "Testing dsda-doom directly..."
cd "$SCRIPT_DIR/doom"
dsda-doom -iwad DOOM.WAD
EOF

cat >"$DOOMBOX_DIR/test_doom.sh" <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo "Testing DOOM via lzdoom wrapper..."
cd "$SCRIPT_DIR/doom"
"$SCRIPT_DIR/lzdoom" -iwad DOOM.WAD
EOF

cat >"$DOOMBOX_DIR/fix_numpy.sh" <<'EOF'
#!/bin/bash
# Fix NumPy compatibility issues with OpenCV
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

echo "Fixing NumPy compatibility issues..."
source venv/bin/activate

echo "Uninstalling incompatible packages..."
pip uninstall -y numpy opencv-python 2>/dev/null || true

echo "Installing NumPy 1.x..."
pip install "numpy<2.0.0"

echo "Reinstalling OpenCV..."
pip install opencv-python==4.8.1.78

echo "Testing import..."
python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')"

echo "Fix complete!"
EOF

cat >"$DOOMBOX_DIR/debug_controller.sh" <<'EOF'
#!/bin/bash
echo "DualShock 4 Controller Debug Info"
echo "=================================="

# Check if controller is detected
echo "Checking for controllers..."
ls /dev/input/js* 2>/dev/null || echo "No joystick devices found"

# Check bluetooth status
echo -e "\nBluetooth status:"
systemctl is-active bluetooth 2>/dev/null || echo "Bluetooth service not available"

# List connected devices
echo -e "\nConnected bluetooth devices:"
bluetoothctl devices Connected 2>/dev/null || echo "bluetoothctl not available"

# Test joystick if available
if ls /dev/input/js* &>/dev/null; then
    echo -e "\nTesting first joystick (press Ctrl+C to exit):"
    timeout 10 jstest /dev/input/js0 || echo "jstest failed or timed out"
fi

echo -e "\nPython pygame joystick test:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 -c "
import pygame
pygame.init()
pygame.joystick.init()
print(f'Number of joysticks: {pygame.joystick.get_count()}')
if pygame.joystick.get_count() > 0:
    joy = pygame.joystick.Joystick(0)
    joy.init()
    print(f'Joystick name: {joy.get_name()}')
    print(f'Buttons: {joy.get_numbuttons()}')
    print(f'Axes: {joy.get_numaxes()}')
pygame.quit()
"
EOF

cat >"$DOOMBOX_DIR/view_scores.sh" <<'EOF'
#!/bin/bash
echo "DoomBox High Scores"
echo "===================="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

if [ -f scores.db ]; then
    sqlite3 scores.db "SELECT
        ROW_NUMBER() OVER (ORDER BY score DESC) as rank,
        player_name,
        score,
        datetime(timestamp) as date_played,
        level_reached
    FROM scores
    ORDER BY score DESC
    LIMIT 20;"
else
    echo "No scores database found. Play some games first!"
fi
EOF

# Make all scripts executable
chmod +x "$DOOMBOX_DIR"/*.sh

# Asset summary
echo -e "${YELLOW}Asset Summary:${NC}"
FONT_COUNT=$(find "$FONTS_DIR" -name "*.ttf" -o -name "*.otf" 2>/dev/null | wc -l)
VIDEO_COUNT=$(find "$SCRIPT_DIR/vid" -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.mkv" 2>/dev/null | wc -l)
IMG_COUNT=$(find "$SCRIPT_DIR/img" -name "*.jpg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | wc -l)

echo -e "Fonts: $FONT_COUNT files (copied to app)"
echo -e "Videos: $VIDEO_COUNT files (using from git repo)"
echo -e "Images: $IMG_COUNT files (using from git repo)"

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Setup Complete!"
echo -e "=========================================="
echo -e "Application built in: ${YELLOW}$DOOMBOX_DIR${NC}"
echo -e ""
echo -e "Assets loaded:"
echo -e "• Video backgrounds ($VIDEO_COUNT videos - using from git repo)"
echo -e "• Custom fonts ($FONT_COUNT fonts - copied to app)"
echo -e "• Image assets ($IMG_COUNT images - using from git repo)"
echo -e ""
echo -e "To run DoomBox:"
echo -e "1. ${YELLOW}Test the kiosk:${NC}"
echo -e "   cd $DOOMBOX_DIR && ./test_kiosk.sh"
echo -e ""
echo -e "2. ${YELLOW}Test DOOM engine:${NC}"
echo -e "   cd $DOOMBOX_DIR && ./test_doom.sh"
echo -e ""
echo -e "3. ${YELLOW}Start with X server:${NC}"
echo -e "   cd $DOOMBOX_DIR && ./start_with_x.sh"
echo -e ""
echo -e "4. ${YELLOW}Setup controller:${NC}"
echo -e "   cd $DOOMBOX_DIR && ./setup_controller.sh"
echo -e ""
echo -e "5. ${YELLOW}Pair DualShock 4 controller:${NC}"
echo -e "   cd $DOOMBOX_DIR && ./pair_controller.sh"
echo -e ""
echo -e "Available scripts in $DOOMBOX_DIR:"
echo -e "• start.sh - Main kiosk launcher"
echo -e "• start_with_x.sh - Start with X server"
echo -e "• test_kiosk.sh - Test kiosk application"
echo -e "• test_doom.sh - Test DOOM engine"
echo -e "• setup_controller.sh - Controller setup helper"
echo -e "• pair_controller.sh - Pair DualShock 4 controller"
echo -e "• debug_controller.sh - Controller debugging"
echo -e "• auto_connect_controller.sh - Auto-connect controller"
echo -e "• view_scores.sh - View high scores"
echo -e "• fix_numpy.sh - Fix NumPy compatibility issues"
echo -e ""
echo -e "DOOM files:"
echo -e "• DOOM.WAD location: $DOOM_DIR/DOOM.WAD"
echo -e "• DOOM wrapper: $DOOMBOX_DIR/lzdoom"
echo -e ""
echo -e "${GREEN}Ready to play!${NC}"
echo -e "${NC}"
