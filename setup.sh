#!/bin/bash

# shmegl's DoomBox Setup Script
# For Radxa Zero running Debian 12 (DietPI)
# Run as root: sudo bash setup.sh

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo bash setup.sh)${NC}"
    exit 1
fi

# Get the directory where this script is located (should be repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo -e "${YELLOW}Running from: $SCRIPT_DIR${NC}"

# Define paths
DOOMBOX_DIR="/opt/doombox"
DOOM_DIR="$DOOMBOX_DIR/doom"
LOGS_DIR="$DOOMBOX_DIR/logs"
FONTS_DIR="$DOOMBOX_DIR/fonts"
VID_DIR="$DOOMBOX_DIR/vid"
IMG_DIR="$DOOMBOX_DIR/img"

echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$DOOMBOX_DIR"
mkdir -p "$DOOM_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$FONTS_DIR"
mkdir -p "$VID_DIR"
mkdir -p "$IMG_DIR"

echo -e "${YELLOW}Updating system packages...${NC}"
apt update
apt upgrade -y

echo -e "${YELLOW}Installing system dependencies...${NC}"
apt install -y \
    git \
    wget \
    curl \
    unzip \
    bluetooth \
    bluez \
    bluez-tools \
    joystick \
    jstest-gtk \
    feh \
    mosquitto \
    mosquitto-clients \
    sqlite3 \
    dsda-doom \
    doom-wad-shareware \
    python3 \
    python3-pip \
    python3-venv \
    python3-opencv \
    build-essential \
    xorg \
    xinit \
    xfce4 \
    xfce4-goodies \
    libopencv-dev

echo -e "${YELLOW}Installing video processing dependencies...${NC}"
apt install -y ffmpeg libavcodec-dev libavformat-dev libswscale-dev

echo -e "${YELLOW}Setting up DOOM engine (dsda-doom)...${NC}"
# Check for dsda-doom installation
if command -v dsda-doom &>/dev/null; then
    DOOM_ENGINE="dsda-doom"
    echo "Found dsda-doom engine"
elif [ -f "/usr/games/dsda-doom" ]; then
    DOOM_ENGINE="/usr/games/dsda-doom"
    echo "Found dsda-doom in /usr/games/"
else
    echo -e "${RED}dsda-doom not found! Installing from source...${NC}"
    # Install dsda-doom from source if not available in packages
    cd /tmp
    git clone https://github.com/kraflab/dsda-doom.git
    cd dsda-doom
    apt install -y cmake libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-net-dev
    mkdir build && cd build
    cmake ..
    make -j4
    make install
    DOOM_ENGINE="dsda-doom"
fi

echo "Using DOOM engine: $DOOM_ENGINE"

# Create lzdoom compatibility wrapper script for existing kiosk code
echo "Creating lzdoom compatibility wrapper for dsda-doom..."
cat >/usr/local/bin/lzdoom <<'EOF'
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
mkdir -p /opt/doombox/logs

# Log the command for debugging
echo "$(date): DOOM Command: ${DOOM_CMD[*]}" >> /opt/doombox/logs/doom.log

# Execute dsda-doom
exec "${DOOM_CMD[@]}"
EOF

chmod +x /usr/local/bin/lzdoom
echo -e "${GREEN}dsda-doom installed with lzdoom compatibility wrapper!${NC}"

echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
cd "$DOOMBOX_DIR"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Installing Python dependencies with video support...${NC}"
pip install --upgrade pip
cat >requirements.txt <<'EOF'
flask==2.3.3
qrcode[pil]==7.4.2
pygame==2.5.2
requests==2.31.0
paho-mqtt==1.6.1
pillow==10.0.1
psutil==5.9.6
opencv-python==4.8.1.78
EOF

pip install -r requirements.txt

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

# Check if we're running from within the repository
if [ -f "$SCRIPT_DIR/kiosk.py" ]; then
    echo "Found kiosk.py in repository, copying files..."

    # Copy main application files
    cp "$SCRIPT_DIR/kiosk.py" ./
    [ -f "$SCRIPT_DIR/config.py" ] && cp "$SCRIPT_DIR/config.py" ./
    [ -f "$SCRIPT_DIR/webhook.py" ] && cp "$SCRIPT_DIR/webhook.py" ./

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

    # Copy videos
    if [ -d "$SCRIPT_DIR/vid" ]; then
        echo -e "${YELLOW}Copying demo videos...${NC}"
        cp -r "$SCRIPT_DIR/vid"/* "$VID_DIR/"
        echo -e "${GREEN}✅ Demo videos copied:${NC}"
        ls -la "$VID_DIR/" | grep -E "\.(mp4|avi|mov|mkv)$" | wc -l | xargs echo "   Video files:"

        # Set proper permissions for video files
        chmod 644 "$VID_DIR"/*.mp4 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  No vid directory found in repo${NC}"
    fi

    # Copy images
    if [ -d "$SCRIPT_DIR/img" ]; then
        echo -e "${YELLOW}Copying image assets...${NC}"
        cp -r "$SCRIPT_DIR/img"/* "$IMG_DIR/"
        echo -e "${GREEN}✅ Image assets copied${NC}"
    else
        echo -e "${YELLOW}⚠️  No img directory found in repo${NC}"
    fi

    # Copy any additional assets
    [ -f "$SCRIPT_DIR/lmao.gif" ] && cp "$SCRIPT_DIR/lmao.gif" ./
    [ -f "$SCRIPT_DIR/formsubmit.jpg" ] && cp "$SCRIPT_DIR/formsubmit.jpg" ./

    echo -e "${GREEN}Repository files copied successfully!${NC}"
else
    echo -e "${YELLOW}Repository files not found."
    echo -e "Please ensure you're running setup.sh from the cloned repository directory.${NC}"
    echo -e "${YELLOW}Creating minimal kiosk.py...${NC}"

    # Create a minimal working kiosk if repo files aren't found
    cat >kiosk.py <<'EOF'
#!/usr/bin/env python3
"""
Minimal DoomBox Kiosk - Please replace with full version from repository
"""
import pygame
import sys

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 960), pygame.FULLSCREEN)
    pygame.display.set_caption("DoomBox - Missing Files")

    font = pygame.font.Font(None, 48)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

        screen.fill((0, 0, 0))
        text = font.render("DoomBox Setup Incomplete", True, (255, 0, 0))
        text2 = font.render("Please copy files from repository", True, (255, 255, 255))
        text3 = font.render("Press ESC to exit", True, (128, 128, 128))

        screen.blit(text, (320, 400))
        screen.blit(text2, (200, 450))
        screen.blit(text3, (500, 500))

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
EOF
    chmod +x kiosk.py
fi

echo -e "${YELLOW}Setting up Mosquitto MQTT broker...${NC}"
systemctl enable mosquitto
systemctl start mosquitto

# Configure mosquitto for local access
cat >/etc/mosquitto/conf.d/doombox.conf <<'EOF'
# DoomBox MQTT Configuration
listener 1883 localhost
allow_anonymous true
EOF

systemctl restart mosquitto

echo -e "${YELLOW}Creating systemd service...${NC}"
cat >/etc/systemd/system/doombox.service <<'EOF'
[Unit]
Description=shmegl's DoomBox Kiosk
After=multi-user.target graphical.target mosquitto.service
Wants=graphical.target
Requires=mosquitto.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/doombox
ExecStart=/opt/doombox/start.sh
Restart=always
RestartSec=5
Environment=HOME=/root
Environment=DISPLAY=:0

[Install]
WantedBy=graphical.target
EOF

echo -e "${YELLOW}Creating startup scripts...${NC}"
cat >"$DOOMBOX_DIR/start.sh" <<'EOF'
#!/bin/bash
# DoomBox Kiosk Startup Script

# Ensure we're in the right directory
cd /opt/doombox

# Activate Python virtual environment
source venv/bin/activate

# Set display
export DISPLAY=:0

# Wait for display to be ready
timeout=30
while [ $timeout -gt 0 ]; do
    if xset q &>/dev/null; then
        echo "Display ready"
        break
    fi
    echo "Waiting for display... ($timeout)"
    sleep 1
    ((timeout--))
done

# Start the kiosk application
echo "Starting DoomBox Kiosk..."
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/start.sh"

cat >"$DOOMBOX_DIR/start_x_display.sh" <<'EOF'
#!/bin/bash
# Start X server and DoomBox kiosk
export DISPLAY=:0
cd /opt/doombox

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
unclutter -idle 1 -root &

# Start the kiosk
./start.sh
EOF

chmod +x "$DOOMBOX_DIR/start_x_display.sh"

# Helper scripts for testing
cat >"$DOOMBOX_DIR/test_kiosk.sh" <<'EOF'
#!/bin/bash
cd /opt/doombox
source venv/bin/activate
export DISPLAY=:0
echo "Testing DoomBox Kiosk..."
python kiosk.py
EOF

cat >"$DOOMBOX_DIR/test_dsda_doom.sh" <<'EOF'
#!/bin/bash
echo "Testing dsda-doom directly..."
cd /opt/doombox/doom
dsda-doom -iwad DOOM.WAD
EOF

cat >"$DOOMBOX_DIR/test_doom.sh" <<'EOF'
#!/bin/bash
echo "Testing DOOM via lzdoom wrapper..."
cd /opt/doombox/doom
/usr/local/bin/lzdoom -iwad DOOM.WAD
EOF

cat >"$DOOMBOX_DIR/pair_controller.sh" <<'EOF'
#!/bin/bash
echo "Starting Bluetooth controller pairing..."
echo "Put your DualShock 4 in pairing mode (hold Share + PS buttons)"
echo "Press Ctrl+C to exit"

# Enable bluetooth
systemctl start bluetooth
bluetoothctl power on
bluetoothctl agent on
bluetoothctl default-agent
bluetoothctl scan on

echo "Bluetooth scanning started. Look for your controller and use:"
echo "bluetoothctl pair [MAC_ADDRESS]"
echo "bluetoothctl trust [MAC_ADDRESS]"
echo "bluetoothctl connect [MAC_ADDRESS]"

bluetoothctl
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
systemctl is-active bluetooth

# List connected devices
echo -e "\nConnected bluetooth devices:"
bluetoothctl devices Connected

# Test joystick if available
if ls /dev/input/js* &>/dev/null; then
    echo -e "\nTesting first joystick (press Ctrl+C to exit):"
    timeout 10 jstest /dev/input/js0 || echo "jstest failed or timed out"
fi

echo -e "\nPython pygame joystick test:"
cd /opt/doombox
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
cd /opt/doombox

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

cat >"$DOOMBOX_DIR/start_kiosk_service.sh" <<'EOF'
#!/bin/bash
echo "Starting DoomBox Service..."
systemctl start doombox
systemctl status doombox
echo "To view logs: journalctl -u doombox -f"
EOF

cat >"$DOOMBOX_DIR/stop_kiosk_service.sh" <<'EOF'
#!/bin/bash
echo "Stopping DoomBox Service..."
systemctl stop doombox
systemctl status doombox
EOF

# Make all scripts executable
chmod +x "$DOOMBOX_DIR"/*.sh

echo -e "${YELLOW}Creating XFCE desktop entries...${NC}"

# Define desktop entries for XFCE Applications Menu
DESKTOP_ENTRIES=(
    "doombox-kiosk.desktop:DoomBox Kiosk:Main kiosk application:/opt/doombox/test_kiosk.sh:application-x-addon:false:AudioVideo;Game"
    "doombox-test-doom-wrapper.desktop:Test DOOM (Wrapper):Test DOOM via lzdoom wrapper:/opt/doombox/test_doom.sh:applications-games:true:Game"
    "doombox-test-dsda-doom.desktop:Test dsda-doom (Direct):Test dsda-doom directly:/opt/doombox/test_dsda_doom.sh:applications-games:true:Game"
    "doombox-debug-controller.desktop:Debug Controller:Test controller input:/opt/doombox/debug_controller.sh:input-gaming:true:System;HardwareSettings"
    "doombox-pair-controller.desktop:Pair Controller:Bluetooth pairing helper:/opt/doombox/pair_controller.sh:bluetooth:true:System;HardwareSettings"
    "doombox-view-scores.desktop:View High Scores:Database viewer:/opt/doombox/view_scores.sh:trophy-gold:true:Game;Database"
    "doombox-start-service.desktop:Start Kiosk Service:Start the kiosk service:/opt/doombox/start_kiosk_service.sh:media-playback-start:true:System"
    "doombox-stop-service.desktop:Stop Kiosk Service:Stop the kiosk service:/opt/doombox/stop_kiosk_service.sh:media-playback-stop:true:System"
    "doombox-start-display.desktop:Start X Display:X11 startup helper:/opt/doombox/start_x_display.sh:video-display:true:System"
)

# Function to create desktop entry
create_desktop_entry() {
    local filename="$1"
    local name="$2"
    local comment="$3"
    local exec="$4"
    local icon="$5"
    local terminal="$6"
    local categories="$7"

    cat >"/usr/share/applications/$filename" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$name
Comment=$comment
Exec=$exec
Icon=$icon
Terminal=$terminal
Categories=$categories
EOF
}

# Create all desktop entries
for entry in "${DESKTOP_ENTRIES[@]}"; do
    IFS=':' read -r filename name comment exec icon terminal categories <<<"$entry"
    create_desktop_entry "$filename" "$name" "$comment" "$exec" "$icon" "$terminal" "$categories"
    echo "Created desktop entry: $name"
done

echo -e "${YELLOW}Updating desktop database...${NC}"
update-desktop-database /usr/share/applications

echo -e "${YELLOW}Setting up XFCE auto-start...${NC}"
mkdir -p /etc/xdg/autostart
cat >/etc/xdg/autostart/doombox-kiosk.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=DoomBox Kiosk
Comment=Auto-start DoomBox kiosk application
Exec=/opt/doombox/start.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo -e "${YELLOW}Setting up auto-login for root user...${NC}"
# Configure auto-login for DietPi/Debian
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat >/etc/systemd/system/getty@tty1.service.d/override.conf <<'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOF

echo -e "${YELLOW}Setting permissions...${NC}"
chown -R root:root "$DOOMBOX_DIR"
chmod -R 755 "$DOOMBOX_DIR"

# Make sure scripts are executable
find "$DOOMBOX_DIR" -name "*.sh" -exec chmod +x {} \;

echo -e "${YELLOW}Reloading systemd and enabling services...${NC}"
systemctl daemon-reload

# Asset summary
echo -e "${YELLOW}Asset Summary:${NC}"
FONT_COUNT=$(find "$FONTS_DIR" -name "*.ttf" -o -name "*.otf" 2>/dev/null | wc -l)
VIDEO_COUNT=$(find "$VID_DIR" -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.mkv" 2>/dev/null | wc -l)
IMG_COUNT=$(find "$IMG_DIR" -name "*.jpg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | wc -l)

echo -e "Fonts: $FONT_COUNT files"
echo -e "Videos: $VIDEO_COUNT files"
echo -e "Images: $IMG_COUNT files"

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Setup Complete!"
echo -e "=========================================="
echo -e "Repository files: ${GREEN}$([ -f "$SCRIPT_DIR/kiosk.py" ] && echo "✓ Found and copied" || echo "✗ Not found")${NC}"
echo -e ""
echo -e "Assets loaded:"
echo -e "• Video backgrounds ($VIDEO_COUNT videos)"
echo -e "• Custom fonts ($FONT_COUNT fonts)"
echo -e "• Image assets ($IMG_COUNT images)"
echo -e ""
echo -e "Next steps:"
echo -e "1. ${YELLOW}Start X11 display server:${NC}"
echo -e "   /opt/doombox/start_x_display.sh"
echo -e ""
echo -e "2. ${YELLOW}Test components:${NC}"
echo -e "   - Test kiosk: /opt/doombox/test_kiosk.sh"
echo -e "   - Test DOOM: /opt/doombox/test_doom.sh"
echo -e ""
echo -e "3. ${YELLOW}Pair your DualShock 4 controller:${NC}"
echo -e "   /opt/doombox/pair_controller.sh"
echo -e ""
echo -e "4. ${YELLOW}Start the service:${NC}"
echo -e "   /opt/doombox/start_kiosk_service.sh"
echo -e ""
echo -e "5. ${YELLOW}For auto-boot kiosk mode:${NC}"
echo -e "   systemctl set-default multi-user.target"
echo -e "   systemctl enable doombox.service"
echo -e ""
echo -e "Files created in: $DOOMBOX_DIR"
echo -e "DOOM.WAD location: $DOOM_DIR/DOOM.WAD"
echo -e "Logs directory: $LOGS_DIR"
echo -e "Fonts: $FONTS_DIR ($FONT_COUNT fonts)"
echo -e "Demo videos: $VID_DIR ($VIDEO_COUNT videos)"
echo -e ""
echo -e "${YELLOW}XFCE Applications Menu -> DoomBox${NC} for all tools"
echo -e "${NC}"

# Final check
if [ -f "$DOOMBOX_DIR/kiosk.py" ] && [ -s "$DOOMBOX_DIR/kiosk.py" ]; then
    echo -e "${GREEN}✓ Kiosk application ready${NC}"
else
    echo -e "${RED}✗ Kiosk application needs manual copy from repository${NC}"
fi
