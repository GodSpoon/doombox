#!/bin/bash

# shmegl's DoomBox Setup Script
# For Radxa Zero running Debian 12 (DietPI)
# Run as root: sudo bash setup.sh

set -e

echo "=========================================="
echo "  shmegl's DoomBox Setup"
echo "  Highest score gets a free tattoo!"
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
    python3 \
    python3-pip \
    python3-venv \
    lzdoom \
    git \
    wget \
    curl \
    unzip \
    bluetooth \
    bluez \
    bluez-tools \
    joystick \
    jstest-gtk \
    xorg \
    xinit \
    xfce4 \
    lightdm \
    chromium-browser \
    feh \
    mosquitto-clients \
    sqlite3

echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
cd "$DOOMBOX_DIR"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
cat > requirements.txt << EOF
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

echo -e "${YELLOW}Creating main kiosk application...${NC}"
cat > "$DOOMBOX_DIR/kiosk.py" << 'EOF'
#!/usr/bin/env python3
"""
shmegl's DoomBox Kiosk Application
Displays QR code, manages game sessions, tracks scores
"""

import pygame
import qrcode
import json
import sqlite3
import subprocess
import time
import threading
import requests
import signal
import sys
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import paho.mqtt.client as mqtt

class DoomBoxKiosk:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Display settings
        self.DISPLAY_SIZE = (1280, 960)
        self.screen = pygame.display.set_mode(self.DISPLAY_SIZE, pygame.FULLSCREEN)
        pygame.display.set_caption("shmegl's DoomBox")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        
        # Paths
        self.base_dir = "/opt/doombox"
        self.doom_dir = f"{self.base_dir}/doom"
        self.db_path = f"{self.base_dir}/scores.db"
        
        # Game state
        self.current_player = None
        self.game_running = False
        
        # Controller
        self.controller = None
        self.konami_sequence = [
            pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
            pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT,
            pygame.K_b, pygame.K_a  # B, A on controller
        ]
        self.konami_input = []
        
        # Initialize database
        self.init_database()
        
        # Generate QR code
        self.qr_image = self.generate_qr_code()
        
        # Start MQTT listener (optional)
        self.setup_mqtt()
        
        print("DoomBox Kiosk initialized")

    def init_database(self):
        """Initialize SQLite database for scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                level_reached INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        conn.close()

    def generate_qr_code(self):
        """Generate QR code for the registration form"""
        # Replace with your actual GitHub Pages URL
        form_url = "https://your-username.github.io/doombox-form/"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(form_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((300, 300))
        
        # Convert PIL image to pygame surface
        qr_surface = pygame.image.fromstring(qr_img.tobytes(), qr_img.size, qr_img.mode)
        return qr_surface

    def setup_mqtt(self):
        """Setup MQTT client for remote game triggers"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            # Connect to local mosquitto broker
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"MQTT setup failed: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        print(f"MQTT connected with result code {rc}")
        client.subscribe("doombox/start_game")

    def on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            data = json.loads(msg.payload.decode())
            player_name = data.get('player_name', 'Unknown')
            print(f"MQTT: Starting game for {player_name}")
            self.start_game(player_name)
        except Exception as e:
            print(f"MQTT message error: {e}")

    def setup_controller(self):
        """Setup DualShock 4 controller"""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            print(f"Controller connected: {self.controller.get_name()}")
            return True
        return False

    def get_top_scores(self, limit=10):
        """Get top scores from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT player_name, score, timestamp 
            FROM scores 
            ORDER BY score DESC, timestamp ASC 
            LIMIT ?
        ''', (limit,))
        scores = cursor.fetchall()
        conn.close()
        return scores

    def add_score(self, player_name, score, level=1):
        """Add score to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scores (player_name, score, timestamp, level_reached)
            VALUES (?, ?, ?, ?)
        ''', (player_name, score, datetime.now(), level))
        conn.commit()
        conn.close()
        print(f"Score added: {player_name} - {score}")

    def draw_screen(self):
        """Draw the main kiosk screen"""
        self.screen.fill(self.BLACK)
        
        # Title
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 32)
        
        title = font_large.render("shmegl's DoomBox", True, self.RED)
        subtitle = font_medium.render("Highest score gets a free tattoo!", True, self.WHITE)
        instruction = font_small.render("Scan the QR code and fill out the form to play", True, self.GREEN)
        
        # Center title elements
        self.screen.blit(title, (self.DISPLAY_SIZE[0]//2 - title.get_width()//2, 50))
        self.screen.blit(subtitle, (self.DISPLAY_SIZE[0]//2 - subtitle.get_width()//2, 130))
        self.screen.blit(instruction, (self.DISPLAY_SIZE[0]//2 - instruction.get_width()//2, 180))
        
        # QR Code
        qr_x = 100
        qr_y = 250
        self.screen.blit(self.qr_image, (qr_x, qr_y))
        
        # Top scores
        scores = self.get_top_scores()
        scores_title = font_medium.render("TOP SCORES", True, self.YELLOW)
        self.screen.blit(scores_title, (500, 250))
        
        y_offset = 300
        for i, (name, score, timestamp) in enumerate(scores):
            color = self.YELLOW if i == 0 else self.WHITE
            score_text = font_small.render(f"{i+1}. {name}: {score}", True, color)
            self.screen.blit(score_text, (500, y_offset + i * 35))
        
        # Status text
        if self.game_running:
            status_text = font_medium.render(f"PLAYING: {self.current_player}", True, self.GREEN)
            self.screen.blit(status_text, (self.DISPLAY_SIZE[0]//2 - status_text.get_width()//2, 800))
        
        pygame.display.flip()

    def handle_controller_input(self):
        """Handle controller input including Konami code"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                # Check Konami code
                self.konami_input.append(event.key)
                if len(self.konami_input) > len(self.konami_sequence):
                    self.konami_input.pop(0)
                
                if self.konami_input == self.konami_sequence:
                    print("Konami code activated!")
                    self.start_game("TEST_PLAYER")
                    self.konami_input = []
            
            elif event.type == pygame.JOYBUTTONDOWN:
                if self.controller:
                    # Map controller buttons to keyboard events for Konami code
                    button_map = {
                        0: pygame.K_a,      # X button -> A
                        1: pygame.K_b,      # Circle -> B
                        # Add more mappings as needed
                    }
                    
                    if event.button in button_map:
                        mapped_key = button_map[event.button]
                        self.konami_input.append(mapped_key)
                        
                        if len(self.konami_input) > len(self.konami_sequence):
                            self.konami_input.pop(0)
                        
                        if self.konami_input == self.konami_sequence:
                            print("Konami code activated!")
                            self.start_game("TEST_PLAYER")
                            self.konami_input = []
        
        return True

    def start_game(self, player_name):
        """Start DOOM game with player name"""
        if self.game_running:
            print("Game already running!")
            return
        
        self.current_player = player_name
        self.game_running = True
        
        print(f"Starting DOOM for player: {player_name}")
        
        # Launch DOOM in a separate thread
        game_thread = threading.Thread(target=self._run_doom, args=(player_name,))
        game_thread.daemon = True
        game_thread.start()

    def _run_doom(self, player_name):
        """Run DOOM game in subprocess"""
        try:
            # DOOM command
            doom_cmd = [
                'lzdoom',
                '-iwad', f'{self.doom_dir}/DOOM.WAD',
                '-width', '640',
                '-height', '480',
                '-fullscreen',
                '+name', player_name
            ]
            
            print(f"Launching DOOM: {' '.join(doom_cmd)}")
            
            # Run DOOM
            process = subprocess.Popen(doom_cmd, cwd=self.doom_dir)
            process.wait()
            
            # Game ended, extract score (this is simplified)
            # In a real implementation, you'd parse DOOM's output or save files
            score = self._extract_score()
            
            if not player_name.startswith("TEST_"):
                self.add_score(player_name, score)
            
            print(f"Game ended. Score: {score}")
            
        except Exception as e:
            print(f"Error running DOOM: {e}")
        finally:
            self.game_running = False
            self.current_player = None

    def _extract_score(self):
        """Extract score from DOOM (simplified implementation)"""
        # This is a placeholder - in reality you'd need to:
        # 1. Parse DOOM's save files
        # 2. Use DOOM's demo recording features
        # 3. Implement a custom DOOM mod that writes scores
        import random
        return random.randint(1000, 50000)

    def check_for_new_players(self):
        """Check for new players via webhook/API/file"""
        # This could check:
        # 1. A local file written by a webhook
        # 2. An API endpoint
        # 3. MQTT messages (already implemented)
        
        try:
            # Example: Check for a trigger file
            trigger_file = f"{self.base_dir}/new_player.json"
            if os.path.exists(trigger_file):
                with open(trigger_file, 'r') as f:
                    data = json.load(f)
                
                player_name = data.get('player_name', 'Unknown')
                self.start_game(player_name)
                
                # Remove trigger file
                os.remove(trigger_file)
        except Exception as e:
            print(f"Error checking for new players: {e}")

    def run(self):
        """Main kiosk loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("Starting DoomBox kiosk...")
        
        while running:
            # Setup controller if not connected
            if not self.controller:
                self.setup_controller()
            
            # Handle input
            running = self.handle_controller_input()
            
            # Check for new players
            self.check_for_new_players()
            
            # Draw screen
            self.draw_screen()
            
            # Limit FPS
            clock.tick(30)
        
        pygame.quit()
        sys.exit()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down DoomBox...")
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    # Change to doombox directory
    os.chdir("/opt/doombox")
    
    kiosk = DoomBoxKiosk()
    kiosk.run()
EOF

echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/doombox.service << EOF
[Unit]
Description=shmegl's DoomBox Kiosk
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/doombox
Environment=DISPLAY=:0
ExecStart=/opt/doombox/venv/bin/python /opt/doombox/kiosk.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

echo -e "${YELLOW}Creating startup script...${NC}"
cat > "$DOOMBOX_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox
source venv/bin/activate
export DISPLAY=:0
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/start.sh"

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

# You'll need to manually pair the controller
echo "Run 'bluetoothctl' and use these commands:"
echo "  scan on"
echo "  pair [MAC_ADDRESS]"
echo "  trust [MAC_ADDRESS]"
echo "  connect [MAC_ADDRESS]"
EOF

chmod +x "$DOOMBOX_DIR/pair_controller.sh"

echo -e "${YELLOW}Setting up auto-login and kiosk mode...${NC}"
# Configure LightDM for auto-login
cat > /etc/lightdm/lightdm.conf.d/50-doombox.conf << EOF
[Seat:*]
autologin-user=root
autologin-user-timeout=0
user-session=xfce
EOF

# Create autostart entry
mkdir -p /root/.config/autostart
cat > /root/.config/autostart/doombox.desktop << EOF
[Desktop Entry]
Type=Application
Name=DoomBox
Exec=/opt/doombox/start.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo -e "${YELLOW}Creating test scripts...${NC}"
cat > "$DOOMBOX_DIR/test_doom.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox/doom
lzdoom -iwad DOOM.WAD -width 640 -height 480 +name TEST_PLAYER
EOF

chmod +x "$DOOMBOX_DIR/test_doom.sh"

cat > "$DOOMBOX_DIR/test_kiosk.sh" << 'EOF'
#!/bin/bash
cd /opt/doombox
source venv/bin/activate
python kiosk.py
EOF

chmod +x "$DOOMBOX_DIR/test_kiosk.sh"

echo -e "${YELLOW}Setting permissions...${NC}"
chown -R root:root "$DOOMBOX_DIR"
chmod +x "$DOOMBOX_DIR/kiosk.py"

echo -e "${YELLOW}Enabling services...${NC}"
systemctl daemon-reload
systemctl enable doombox.service

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Setup Complete!"
echo -e "=========================================="
echo -e "Files created in: $DOOMBOX_DIR"
echo -e ""
echo -e "Next steps:"
echo -e "1. Update the QR code URL in kiosk.py"
echo -e "2. Pair your DualShock 4 controller:"
echo -e "   ${DOOMBOX_DIR}/pair_controller.sh"
echo -e "3. Test DOOM: ${DOOMBOX_DIR}/test_doom.sh"
echo -e "4. Test kiosk: ${DOOMBOX_DIR}/test_kiosk.sh"
echo -e "5. Reboot to start kiosk automatically"
echo -e ""
echo -e "The kiosk will auto-start on boot."
echo -e "Press Ctrl+C to exit kiosk mode."
echo -e "Use Konami code on controller for test games!"
echo -e "${NC}"

echo -e "${YELLOW}Setup complete! Reboot to start the kiosk.${NC}"
