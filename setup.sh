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
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo bash setup.sh)${NC}"
    exit 1
fi

# Define paths
DOOMBOX_DIR="/opt/doombox"
DOOM_DIR="$DOOMBOX_DIR/doom"
LOGS_DIR="$DOOMBOX_DIR/logs"

echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$DOOMBOX_DIR"
mkdir -p "$DOOM_DIR"
mkdir -p "$LOGS_DIR"

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
    mosquitto-clients \
    sqlite3 \
    dsda-doom \
    doom-wad-shareware \
    python3 \
    python3-pip \
    python3-venv \
    build-essential

echo -e "${YELLOW}Setting up DOOM engine (dsda-doom)...${NC}"
# Check for dsda-doom installation
if command -v dsda-doom &> /dev/null; then
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
cat > /usr/local/bin/lzdoom << 'EOF'
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

echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
cat > requirements.txt << 'EOF'
flask==2.3.3
qrcode[pil]==7.4.2
pygame==2.5.2
requests==2.31.0
paho-mqtt==1.6.1
pillow==10.0.1
psutil==5.9.6
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

echo -e "${YELLOW}Cloning main kiosk application from repository...${NC}"
cd "$DOOMBOX_DIR"
# Note: Replace with actual repository URL when available
# git clone https://github.com/your-username/doombox-kiosk.git .
# For now, we'll create a placeholder
echo "# Main kiosk application will be cloned from repository" > kiosk.py
echo "# Repository URL: https://github.com/your-username/doombox-kiosk" >> kiosk.py

echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/doombox.service << 'EOF'
[Unit]
Description=shmegl's DoomBox Kiosk
After=multi-user.target graphical.target
Wants=graphical.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/doombox
ExecStart=/opt/doombox/start_x.sh
Restart=always
RestartSec=5
Environment=HOME=/root
Environment=DISPLAY=:0

[Install]
WantedBy=graphical.target
EOF

echo -e "${YELLOW}Creating startup scripts...${NC}"
cat > "$DOOMBOX_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox
source venv/bin/activate
export DISPLAY=:0
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/start.sh"

cat > "$DOOMBOX_DIR/start_x.sh" << 'EOF'
#!/bin/bash
# Start X server and DoomBox kiosk
export DISPLAY=:0
cd /opt/doombox

# Start X server in background if not running
if ! pgrep -x "Xorg" > /dev/null; then
    startx /opt/doombox/start.sh -- :0 -nolisten tcp &
    sleep 5
fi

# Wait for X to be ready
while ! xset q &>/dev/null; do
    sleep 1
done

# Start the kiosk application
source venv/bin/activate
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/start_x.sh"

echo -e "${YELLOW}Setting up Bluetooth for DualShock 4...${NC}"
# Enable Bluetooth service
systemctl enable bluetooth
systemctl start bluetooth

# Add controller pairing script
cat > "$DOOMBOX_DIR/pair_controller.sh" << 'EOF'
#!/bin/bash
echo "Put DualShock 4 in pairing mode (hold Share + PS buttons)"
echo "Press Enter when ready..."
read

# Scan for devices
timeout 10 bluetoothctl scan on

# Instructions for manual pairing
echo "Run 'bluetoothctl' and use these commands:"
echo "  scan on"
echo "  pair [MAC_ADDRESS]"
echo "  trust [MAC_ADDRESS]"
echo "  connect [MAC_ADDRESS]"
EOF

chmod +x "$DOOMBOX_DIR/pair_controller.sh"

echo -e "${YELLOW}Creating test scripts...${NC}"
cat > "$DOOMBOX_DIR/test_doom.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox/doom
export DISPLAY=:0
/usr/local/bin/lzdoom -iwad DOOM.WAD -width 640 -height 480 +name TEST_PLAYER
EOF

chmod +x "$DOOMBOX_DIR/test_doom.sh"

cat > "$DOOMBOX_DIR/test_kiosk.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox
source venv/bin/activate
export DISPLAY=:0
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/test_kiosk.sh"

cat > "$DOOMBOX_DIR/test_dsda_doom.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox/doom
export DISPLAY=:0
dsda-doom -iwad DOOM.WAD -width 640 -height 480 -playername TEST_DIRECT
EOF

chmod +x "$DOOMBOX_DIR/test_dsda_doom.sh"

cat > "$DOOMBOX_DIR/debug_controller.sh" << 'EOF'
#!/bin/bash
echo "Testing joystick detection..."
ls /dev/input/js*
echo ""
echo "Controller info:"
jstest /dev/input/js0
EOF

chmod +x "$DOOMBOX_DIR/debug_controller.sh"

echo -e "${YELLOW}Creating convenience scripts...${NC}"
cat > "$DOOMBOX_DIR/start_kiosk_service.sh" << 'EOF'
#!/bin/bash
echo "Enabling and starting DoomBox kiosk service..."
systemctl enable doombox.service
systemctl start doombox.service
systemctl status doombox.service
EOF

chmod +x "$DOOMBOX_DIR/start_kiosk_service.sh"

cat > "$DOOMBOX_DIR/stop_kiosk_service.sh" << 'EOF'
#!/bin/bash
echo "Stopping DoomBox kiosk service..."
systemctl stop doombox.service
systemctl disable doombox.service
EOF

chmod +x "$DOOMBOX_DIR/stop_kiosk_service.sh"

cat > "$DOOMBOX_DIR/view_scores.sh" << 'EOF'
#!/bin/bash
echo "DoomBox High Scores:"
echo "==================="
sqlite3 /opt/doombox/scores.db "SELECT player_name, score, timestamp FROM scores ORDER BY score DESC LIMIT 10;"
EOF

chmod +x "$DOOMBOX_DIR/view_scores.sh"

# Function to create desktop entries
create_desktop_entry() {
    local filename="$1"
    local name="$2"
    local comment="$3"
    local exec="$4"
    local icon="$5"
    local terminal="$6"
    local categories="$7"
    
    cat > "/usr/share/applications/${filename}" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=${name}
Comment=${comment}
Exec=${exec}
Icon=${icon}
Terminal=${terminal}
Categories=${categories}
EOF
}

echo -e "${YELLOW}Creating desktop entries for XFCE...${NC}"
mkdir -p /usr/share/applications
mkdir -p /usr/share/desktop-directories

# Create DoomBox category
cat > /usr/share/desktop-directories/DoomBox.directory << 'EOF'
[Desktop Entry]
Version=1.0
Type=Directory
Name=DoomBox
Comment=shmegl's DoomBox Testing and Management Tools
Icon=applications-games
EOF

# Define desktop entries in arrays for easy management
declare -a DESKTOP_ENTRIES=(
    # filename:name:comment:exec:icon:terminal:categories
    "doombox-kiosk.desktop:DoomBox Kiosk:Main DoomBox kiosk application:/opt/doombox/test_kiosk.sh:applications-games:false:Game;DoomBox;"
    "doombox-test-doom.desktop:Test DOOM (Wrapper):Test DOOM via lzdoom compatibility wrapper:/opt/doombox/test_doom.sh:applications-games:false:Game;DoomBox;"
    "doombox-test-dsda.desktop:Test dsda-doom (Direct):Test dsda-doom engine directly:/opt/doombox/test_dsda_doom.sh:applications-games:false:Game;DoomBox;"
    "doombox-debug-controller.desktop:Debug Controller:Test and debug DualShock 4 controller:x-terminal-emulator -e /opt/doombox/debug_controller.sh:input-gaming:true:System;DoomBox;"
    "doombox-pair-controller.desktop:Pair Controller:Pair DualShock 4 controller via Bluetooth:x-terminal-emulator -e /opt/doombox/pair_controller.sh:bluetooth:true:System;DoomBox;"
    "doombox-view-logs.desktop:View DoomBox Logs:View DoomBox system and game logs:x-terminal-emulator -e tail -f /opt/doombox/logs/doom.log:text-x-log:true:System;DoomBox;"
    "doombox-start-service.desktop:Start Kiosk Service:Enable and start the DoomBox kiosk service:x-terminal-emulator -e /opt/doombox/start_kiosk_service.sh:media-playback-start:true:System;DoomBox;"
    "doombox-stop-service.desktop:Stop Kiosk Service:Stop and disable the DoomBox kiosk service:x-terminal-emulator -e /opt/doombox/stop_kiosk_service.sh:media-playback-stop:true:System;DoomBox;"
    "doombox-view-scores.desktop:View High Scores:View DoomBox high scores database:x-terminal-emulator -e /opt/doombox/view_scores.sh:view-list-text:true:System;DoomBox;"
)

# Create all desktop entries
for entry in "${DESKTOP_ENTRIES[@]}"; do
    IFS=':' read -r filename name comment exec icon terminal categories <<< "$entry"
    create_desktop_entry "$filename" "$name" "$comment" "$exec" "$icon" "$terminal" "$categories"
    echo "Created desktop entry: $name"
done

echo -e "${YELLOW}Updating desktop database...${NC}"
update-desktop-database /usr/share/applications

echo -e "${YELLOW}Setting up XFCE menu configuration...${NC}"
# Create custom menu configuration for XFCE
mkdir -p /etc/xdg/menus
cat > /etc/xdg/menus/applications-doombox.menu << 'EOF'
<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
 "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">

<Menu>
  <n>Applications</n>
  <Directory>applications.directory</Directory>

  <!-- DoomBox submenu -->
  <Menu>
    <n>DoomBox</n>
    <Directory>DoomBox.directory</Directory>
    <Include>
      <Category>DoomBox</Category>
    </Include>
  </Menu>

</Menu>
EOF

echo -e "${YELLOW}Setting up auto-login for XFCE (optional)...${NC}"
# Create auto-login configuration for DietPi
if [ -f "/boot/dietpi.txt" ]; then
    echo "AUTO_SETUP_AUTOMATED=1" >> /boot/dietpi.txt
    echo "AUTO_SETUP_GLOBAL_PASSWORD=dietpi" >> /boot/dietpi.txt
fi

echo -e "${YELLOW}Setting permissions...${NC}"
chown -R root:root "$DOOMBOX_DIR"
chmod -R 755 "$DOOMBOX_DIR"

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Setup Complete!"
echo -e "=========================================="
echo -e "Next steps:"
echo -e "1. Clone the main kiosk application:"
echo -e "   cd /opt/doombox"
echo -e "   git clone <your-repo-url> ."
echo -e ""
echo -e "2. Pair your DualShock 4 controller:"
echo -e "   /opt/doombox/pair_controller.sh"
echo -e ""
echo -e "3. Test components:"
echo -e "   - Test dsda-doom: /opt/doombox/test_dsda_doom.sh"
echo -e "   - Test wrapper: /opt/doombox/test_doom.sh"
echo -e "   - Test kiosk: /opt/doombox/test_kiosk.sh"
echo -e ""
echo -e "4. Start the service:"
echo -e "   systemctl enable doombox.service"
echo -e "   systemctl start doombox.service"
echo -e ""
echo -e "5. Check XFCE Applications Menu -> DoomBox"
echo -e "   for all testing and management tools"
echo -e ""
echo -e "Files created in: $DOOMBOX_DIR"
echo -e "DOOM.WAD location: $DOOM_DIR/DOOM.WAD"
echo -e "Logs directory: $LOGS_DIR"
echo -e "${NC}"
