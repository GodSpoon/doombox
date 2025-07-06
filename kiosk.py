#!/usr/bin/env python3
"""
shmegl's DoomBox Kiosk Application - Retro Neocities Style
Now with pixel icons, custom fonts, and video backgrounds!
"""

import pygame
import qrcode
import json
import sqlite3
import subprocess
import time
import threading
import signal
import sys
import os
import math
import logging
import random
import requests
import zipfile
from datetime import datetime
from pathlib import Path
import cv2

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: MQTT not available")

# Set up logging
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(script_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'kiosk.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RetroKioskRenderer:
    """Handles all the retro visual effects and styling"""

    def __init__(self, screen, display_size):
        self.screen = screen
        self.display_size = display_size
        self.frame_count = 0

        # Retro color palette inspired by early web
        self.RETRO_COLORS = {
            'CYBER_GREEN': (0, 255, 0),
            'NEON_PINK': (255, 20, 147),
            'ELECTRIC_BLUE': (0, 191, 255),
            'TERMINAL_AMBER': (255, 191, 0),
            'MATRIX_GREEN': (57, 255, 20),
            'HOT_MAGENTA': (255, 0, 255),
            'LIME_SHOCK': (50, 205, 50),
            'PURPLE_HAZE': (138, 43, 226),
            'FIRE_RED': (255, 69, 0),
            'ICE_BLUE': (176, 224, 230),
            'BLACK': (0, 0, 0),
            'WHITE': (255, 255, 255),
            'GRAY': (128, 128, 128),
            'DARK_GRAY': (64, 64, 64),
            'LIGHT_GRAY': (192, 192, 192)
        }

        # GIF-style effect colors for cycling
        self.rainbow_colors = [
            self.RETRO_COLORS['FIRE_RED'],
            self.RETRO_COLORS['TERMINAL_AMBER'],
            self.RETRO_COLORS['LIME_SHOCK'],
            self.RETRO_COLORS['ELECTRIC_BLUE'],
            self.RETRO_COLORS['PURPLE_HAZE'],
            self.RETRO_COLORS['HOT_MAGENTA']
        ]

        # Animation states
        self.blink_state = 0
        self.scroll_offset = 0

        # Removed sparkle effects for cleaner look

    def get_static_color(self, color_name='TERMINAL_AMBER'):
        """Get static color for clean design"""
        return self.RETRO_COLORS[color_name]

    def draw_clean_border(self, rect, thickness=2):
        """Draw a clean border for overlay boxes"""
        pygame.draw.rect(self.screen, self.RETRO_COLORS['LIGHT_GRAY'], rect, thickness)

    def draw_retro_button(self, rect, text, font, pressed=False):
        """Draw a clean button"""
        x, y, w, h = rect

        if pressed:
            # Pressed state
            pygame.draw.rect(self.screen, self.RETRO_COLORS['DARK_GRAY'], rect)
            text_pos = (x + w//2 - font.size(text)[0]//2 + 1, y + h//2 - font.size(text)[1]//2 + 1)
        else:
            # Normal state
            pygame.draw.rect(self.screen, self.RETRO_COLORS['LIGHT_GRAY'], rect)
            pygame.draw.rect(self.screen, self.RETRO_COLORS['WHITE'], rect, 2)
            text_pos = (x + w//2 - font.size(text)[0]//2, y + h//2 - font.size(text)[1]//2)

        text_surface = font.render(text, True, self.RETRO_COLORS['BLACK'])
        self.screen.blit(text_surface, text_pos)

    def update_frame(self):
        """Update animation frame counter"""
        self.frame_count += 1

class DoomBoxKiosk:
    def __init__(self):
        logger.info("Initializing Retro DoomBox Kiosk...")

        # Initialize pygame
        pygame.init()
        pygame.joystick.init()

        # Display settings optimized for Radxa Zero
        self.DISPLAY_SIZE = (1280, 960)
        try:
            self.screen = pygame.display.set_mode(self.DISPLAY_SIZE, pygame.FULLSCREEN)
            logger.info(f"Display initialized: {self.DISPLAY_SIZE}")
        except pygame.error as e:
            logger.error(f"Fullscreen failed: {e}, trying windowed mode")
            self.screen = pygame.display.set_mode(self.DISPLAY_SIZE)

        pygame.display.set_caption("shmegl's DoomBox - RETRO EDITION")
        pygame.mouse.set_visible(False)

        # Initialize retro renderer
        self.retro = RetroKioskRenderer(self.screen, self.DISPLAY_SIZE)

        # Paths - use relative paths from script location
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_dir = os.path.dirname(self.base_dir)  # Parent directory (git repo)
        self.doom_dir = os.path.join(self.base_dir, "doom")
        self.db_path = os.path.join(self.base_dir, "scores.db")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.trigger_file = os.path.join(self.base_dir, "new_player.json")
        self.fonts_dir = os.path.join(self.base_dir, "fonts")  # Use local fonts first, then fall back to git repo
        self.icons_dir = os.path.join(self.base_dir, "icons")
        self.vid_dir = os.path.join(self.base_dir, "vid")  # Use local vid first, then fall back to git repo
        self.img_dir = os.path.join(self.base_dir, "img")  # Use local img first, then fall back to git repo

        # Fallback to git repo directories if local ones don't exist
        if not os.path.exists(self.fonts_dir):
            self.fonts_dir = os.path.join(self.repo_dir, "fonts")
        if not os.path.exists(self.vid_dir):
            self.vid_dir = os.path.join(self.repo_dir, "vid")
        if not os.path.exists(self.img_dir):
            self.img_dir = os.path.join(self.repo_dir, "img")

        # Ensure directories exist (only create local app directories)
        for dir_path in [self.logs_dir, self.icons_dir]:
            os.makedirs(dir_path, exist_ok=True)

        # Download and setup retro assets
        self.setup_retro_assets()

        # Initialize fonts
        self.setup_retro_fonts()

        # Initialize retro renderer
        self.retro = RetroKioskRenderer(self.screen, self.DISPLAY_SIZE)

        # Load pixel icons
        self.load_pixel_icons()

        # Initialize video background
        self.setup_video_background()

        # Initialize QR code
        self.form_url = "http://shmeglsdoombox.spoon.rip"
        self.generate_qr_code()

        # Initialize database
        self.init_database()

        # Game state
        self.game_running = False
        self.current_player = None
        self.game_process = None

        # Controller setup
        self.controller = None
        self.controller_connected = False
        self.konami_sequence = []
        self.konami_code = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
        self.last_check_time = 0
        self.setup_controller()

        # MQTT setup
        self.mqtt_enabled = MQTT_AVAILABLE
        if self.mqtt_enabled:
            self.setup_mqtt()

        # File monitoring
        self.last_trigger_check = 0

        # Main loop control
        self.running = True
        self.clock = pygame.time.Clock()

        logger.info("Retro DoomBox Kiosk initialized successfully!")

    def setup_retro_assets(self):
        """Download and setup retro fonts and icons"""
        logger.info("Setting up retro assets...")

        # Download Puffin Liquid font (or similar retro font)
        puffin_path = f"{self.fonts_dir}/puffin.ttf"
        if not os.path.exists(puffin_path):
            logger.info("Downloading retro fonts...")
            # For demo, we'll use a free retro font - in production you'd get the actual Puffin Liquid
            # Using a free alternative that has similar retro feel
            try:
                # Create a simple font file placeholder
                # In real implementation, download actual retro fonts
                with open(puffin_path, 'w') as f:
                    f.write("# Placeholder - replace with actual Puffin Liquid font file")
                logger.info("Font placeholder created")
            except Exception as e:
                logger.error(f"Font setup error: {e}")

        # Download Minecraft font
        minecraft_path = f"{self.fonts_dir}/minecraft.ttf"
        if not os.path.exists(minecraft_path):
            try:
                with open(minecraft_path, 'w') as f:
                    f.write("# Placeholder - replace with actual Minecraft font file")
                logger.info("Minecraft font placeholder created")
            except Exception as e:
                logger.error(f"Minecraft font setup error: {e}")

        # Download pixel icons
        icons_zip_path = f"{self.icons_dir}/pixel-icons.zip"
        if not os.path.exists(f"{self.icons_dir}/README.md"):
            logger.info("Setting up pixel icons...")
            try:
                # In real implementation, download from GitHub
                # For now, create placeholder structure
                os.makedirs(f"{self.icons_dir}/16", exist_ok=True)
                os.makedirs(f"{self.icons_dir}/32", exist_ok=True)
                with open(f"{self.icons_dir}/README.md", 'w') as f:
                    f.write("Pixel icons from https://github.com/hackernoon/pixel-icon-library")
                logger.info("Icon structure created")
            except Exception as e:
                logger.error(f"Icon setup error: {e}")

    def setup_retro_fonts(self):
        """Initialize retro fonts with proper sizing for clean layout"""
        try:
            # Try to load custom fonts, fallback to system fonts with retro styling
            try:
                # First check if we have actual font files (not placeholders)
                puffin_path = f"{self.fonts_dir}/Puffin Arcade Liquid.ttf"
                if not os.path.exists(puffin_path):
                    puffin_path = f"{self.fonts_dir}/puffin.ttf"
                
                if os.path.exists(puffin_path) and os.path.getsize(puffin_path) > 100:
                    # Large title font for header (30% of screen height)
                    self.font_huge = pygame.font.Font(puffin_path, 84)
                    self.font_large = pygame.font.Font(puffin_path, 56)
                else:
                    raise FileNotFoundError("No valid Puffin font found")
            except:
                # Fallback to bold system font for retro feel
                self.font_huge = pygame.font.SysFont('arial', 84, bold=True)
                self.font_large = pygame.font.SysFont('arial', 56, bold=True)

            try:
                # Check if we have actual font files (not placeholders)
                minecraft_path = f"{self.fonts_dir}/minecraft.ttf"
                if not os.path.exists(minecraft_path):
                    minecraft_path = f"{self.fonts_dir}/Minecraft.ttf"
                
                if os.path.exists(minecraft_path) and os.path.getsize(minecraft_path) > 100:
                    self.font_medium = pygame.font.Font(minecraft_path, 36)
                    self.font_small = pygame.font.Font(minecraft_path, 28)
                    self.font_tiny = pygame.font.Font(minecraft_path, 22)
                else:
                    raise FileNotFoundError("No valid Minecraft font found")
            except:
                # Fallback to monospace for pixelated feel
                self.font_medium = pygame.font.SysFont('monospace', 36, bold=True)
                self.font_small = pygame.font.SysFont('monospace', 28, bold=True)
                self.font_tiny = pygame.font.SysFont('monospace', 22, bold=True)

            logger.info("Clean layout fonts initialized successfully")
        except Exception as e:
            logger.error(f"Font setup error: {e}")
            # Ultimate fallback
            self.font_huge = pygame.font.Font(None, 84)
            self.font_large = pygame.font.Font(None, 56)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 28)
            self.font_tiny = pygame.font.Font(None, 22)

    def load_pixel_icons(self):
        """Load pixel icons for UI elements"""
        self.icons = {}

        # Updated icon mappings to use actual icons from img/icons directory
        icon_mappings = {
            'skull': 'hockey-mask.png',     # closest to skull
            'fire': 'fire.png',
            'star': 'star.png',
            'trophy': 'trophy.png',
            'controller': 'robot.png',      # closest to gamepad
            'qr': 'code.png',              # closest to QR code
            'wifi': 'globe.png',           # closest to wifi
            'heart': 'heart.png',
            'lightning': 'bolt.png',        # closest to lightning
            'gem': 'sparkles.png'          # closest to gem
        }

        # Check both the icons directory and the img/icons directory
        icon_search_paths = [
            f"{self.icons_dir}/32",
            f"{self.img_dir}/icons"
        ]

        for icon_name, filename in icon_mappings.items():
            icon_loaded = False
            
            # Try to load from available paths
            for search_path in icon_search_paths:
                icon_path = f"{search_path}/{filename}"
                if os.path.exists(icon_path):
                    try:
                        self.icons[icon_name] = pygame.image.load(icon_path)
                        # Scale to 32x32 if needed
                        if self.icons[icon_name].get_size() != (32, 32):
                            self.icons[icon_name] = pygame.transform.scale(self.icons[icon_name], (32, 32))
                        logger.debug(f"Loaded icon: {icon_name} from {icon_path}")
                        icon_loaded = True
                        break
                    except Exception as e:
                        logger.warning(f"Could not load icon {icon_name} from {icon_path}: {e}")
                        continue
            
            # If no icon found, create placeholder
            if not icon_loaded:
                self.icons[icon_name] = self.create_placeholder_icon(32, 32)
                logger.debug(f"Created placeholder for icon: {icon_name}")

        logger.info(f"Loaded {len(self.icons)} pixel icons")

    def create_placeholder_icon(self, width, height):
        """Create a placeholder pixel icon"""
        surface = pygame.Surface((width, height))
        surface.fill((255, 191, 0))  # TERMINAL_AMBER color
        pygame.draw.rect(surface, (0, 0, 0), (2, 2, width-4, height-4), 2)  # BLACK border
        return surface

    def setup_video_background(self):
        """Setup video background from doom demo videos"""
        self.background_video = None
        self.video_frame = None
        self.video_cap = None

        # Look for demo videos in vid directory
        video_files = []
        if os.path.exists(self.vid_dir):
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
                video_files.extend(Path(self.vid_dir).glob(ext))

        if video_files:
            try:
                # Use first available video
                video_path = str(video_files[0])
                self.video_cap = cv2.VideoCapture(video_path)
                logger.info(f"Loaded background video: {video_path}")
            except Exception as e:
                logger.warning(f"Could not load video background: {e}")
                self.video_cap = None
        else:
            logger.info("No demo videos found, using static background")

    def get_video_frame(self):
        """Get current frame from background video"""
        if not self.video_cap:
            return None

        try:
            ret, frame = self.video_cap.read()
            if not ret:
                # Restart video loop
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.video_cap.read()

            if ret:
                # Convert OpenCV BGR to RGB and resize
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, self.DISPLAY_SIZE)

                # Convert to pygame surface
                frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                return frame
        except Exception as e:
            logger.error(f"Video frame error: {e}")
            self.video_cap = None

        return None

    def generate_qr_code(self):
        """Generate QR code with retro styling"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(self.form_url)
            qr.make(fit=True)

            # Create QR image with retro colors
            # Use direct colors since retro renderer might not be ready yet
            qr_img = qr.make_image(fill_color=(57, 255, 20),  # MATRIX_GREEN
                                 back_color=(0, 0, 0))      # BLACK

            # Convert to pygame surface
            qr_string = qr_img.tobytes()
            qr_size = qr_img.size
            self.qr_image = pygame.image.fromstring(qr_string, qr_size, 'RGB')

            logger.info("QR code generated successfully")
        except Exception as e:
            logger.error(f"QR code generation error: {e}")
            # Create placeholder QR
            self.qr_image = pygame.Surface((200, 200))
            self.qr_image.fill((57, 255, 20))  # MATRIX_GREEN

    def init_database(self):
        """Initialize SQLite database for scores"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    level_reached INTEGER DEFAULT 1,
                    time_played INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def setup_controller(self):
        """Setup game controller"""
        try:
            pygame.joystick.quit()
            pygame.joystick.init()

            if pygame.joystick.get_count() > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                self.controller_connected = True
                logger.info(f"Controller connected: {self.controller.get_name()}")
            else:
                self.controller_connected = False
                logger.warning("No controller detected")
        except Exception as e:
            logger.error(f"Controller setup error: {e}")
            self.controller_connected = False

    def setup_mqtt(self):
        """Setup MQTT client for form integration"""
        try:
            # Try new callback API first, fallback to old version
            try:
                self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            except:
                # Fallback for older paho-mqtt versions
                self.mqtt_client = mqtt.Client()
            
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
            self.mqtt_enabled = False

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            client.subscribe("doombox/start_game")
            logger.info("MQTT connected and subscribed")
        else:
            logger.error(f"MQTT connection failed: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        """Handle MQTT messages"""
        try:
            data = json.loads(msg.payload.decode())
            player_name = data.get('player_name', 'Unknown')
            logger.info(f"MQTT trigger received for player: {player_name}")
            self.start_game(player_name)
        except Exception as e:
            logger.error(f"MQTT message error: {e}")

    def check_file_trigger(self):
        """Check for file-based game trigger"""
        if os.path.exists(self.trigger_file):
            try:
                current_mtime = os.path.getmtime(self.trigger_file)
                if current_mtime > self.last_trigger_check:
                    with open(self.trigger_file, 'r') as f:
                        data = json.load(f)

                    player_name = data.get('player_name', 'Unknown')
                    logger.info(f"File trigger received for player: {player_name}")
                    self.start_game(player_name)

                    self.last_trigger_check = current_mtime
            except Exception as e:
                logger.error(f"File trigger error: {e}")

    def check_konami_code(self, input_name):
        """Check for Konami code sequence"""
        self.konami_sequence.append(input_name)

        # Keep only last 10 inputs
        if len(self.konami_sequence) > 10:
            self.konami_sequence.pop(0)

        # Check if sequence matches Konami code
        if len(self.konami_sequence) >= len(self.konami_code):
            if self.konami_sequence[-len(self.konami_code):] == self.konami_code:
                logger.info("Konami code activated!")
                self.start_test_game()
                self.konami_sequence = []

    def get_top_scores(self, limit=10):
        """Get top scores from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT player_name, score, timestamp, level_reached
                FROM scores
                ORDER BY score DESC, timestamp ASC
                LIMIT ?
            ''', (limit,))
            scores = cursor.fetchall()
            conn.close()
            return scores
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []

    def add_score(self, player_name, score, level=1, time_played=0):
        """Add score to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scores (player_name, score, timestamp, level_reached, time_played)
                VALUES (?, ?, ?, ?, ?)
            ''', (player_name, score, datetime.now().isoformat(), level, time_played))
            conn.commit()
            conn.close()
            logger.info(f"Score added: {player_name} - {score}")
        except Exception as e:
            logger.error(f"Database insert error: {e}")

    def start_game(self, player_name):
        """Start DOOM game for player"""
        if self.game_running:
            logger.warning("Game already running, ignoring new request")
            return

        try:
            self.current_player = player_name
            self.game_running = True

            # Command to start DOOM with player name using our wrapper
            lzdoom_path = os.path.join(self.base_dir, "lzdoom")
            doom_cmd = [
                lzdoom_path,
                "-iwad", os.path.join(self.doom_dir, "DOOM.WAD"),
                "-skill", "3",
                "+name", player_name,
                "-fullscreen"
            ]

            logger.info(f"Starting DOOM for player: {player_name}")
            self.game_process = subprocess.Popen(doom_cmd, cwd=self.doom_dir)

            # Monitor game in separate thread
            threading.Thread(target=self.monitor_game, daemon=True).start()

        except Exception as e:
            logger.error(f"Error starting game: {e}")
            self.game_running = False
            self.current_player = None

    def start_test_game(self):
        """Start test game (Konami code)"""
        test_name = f"TEST_{int(time.time()) % 10000}"
        logger.info("Starting test game")
        self.start_game(test_name)

    def monitor_game(self):
        """Monitor DOOM game process"""
        if not self.game_process:
            return

        try:
            return_code = self.game_process.wait()
            logger.info(f"DOOM exited with code: {return_code}")

            # Generate random score for testing
            score = random.randint(100, 9999)

            # Add score to database (skip if test game)
            if self.current_player and not self.current_player.startswith("TEST_"):
                self.add_score(self.current_player, score)
                logger.info(f"Game finished: {self.current_player} scored {score}")
            else:
                logger.info(f"Test game finished: {score} points (not saved)")

        except Exception as e:
            logger.error(f"Game monitoring error: {e}")
        finally:
            self.game_running = False
            self.current_player = None
            self.game_process = None

    def handle_controller_input(self, event):
        """Handle controller input"""
        if not self.controller_connected:
            return

        input_name = None

        if event.type == pygame.JOYBUTTONDOWN:
            button = event.button
            if button == 0:  # X button
                input_name = 'a'
            elif button == 1:  # Circle
                input_name = 'b'

        elif event.type == pygame.JOYHATMOTION:
            hat_value = event.value
            if hat_value == (0, 1):  # Up
                input_name = 'up'
            elif hat_value == (0, -1):  # Down
                input_name = 'down'
            elif hat_value == (-1, 0):  # Left
                input_name = 'left'
            elif hat_value == (1, 0):  # Right
                input_name = 'right'

        if input_name:
            logger.debug(f"Controller input: {input_name}")
            self.check_konami_code(input_name)

    def draw_clean_overlay_box(self, rect, alpha=200):
        """Draw a clean semi-transparent overlay box"""
        overlay = pygame.Surface((rect[2], rect[3]))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        self.screen.blit(overlay, (rect[0], rect[1]))
        
        # Add subtle border
        pygame.draw.rect(self.screen, self.retro.RETRO_COLORS['DARK_GRAY'], rect, 2)

    def draw_retro_screen(self):
        """Draw the main clean kiosk screen optimized for 4:3 display"""
        # Get video background frame
        video_frame = self.get_video_frame()
        if video_frame:
            self.screen.blit(video_frame, (0, 0))
        else:
            # Fallback static background
            self.screen.fill(self.retro.RETRO_COLORS['BLACK'])

        # Calculate layout areas for 4:3 (1280x960) display
        header_height = int(self.DISPLAY_SIZE[1] * 0.3)  # 30% of height for header
        margin = 40
        
        # Header area (top 30%)
        header_rect = (0, 0, self.DISPLAY_SIZE[0], header_height)
        self.draw_clean_overlay_box(header_rect, alpha=180)
        
        # Main title with large Puffin Arcade Liquid font
        title_y = 50
        title_surface = self.font_huge.render("shmegl's DoomBox", True, self.retro.RETRO_COLORS['TERMINAL_AMBER'])
        title_rect = title_surface.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=title_y)
        
        # Add subtle glow effect
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_surface = self.font_huge.render("shmegl's DoomBox", True, self.retro.RETRO_COLORS['DARK_GRAY'])
            self.screen.blit(glow_surface, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle with trophy icon
        subtitle_y = title_y + 100
        trophy_icon = self.icons.get('trophy')
        if trophy_icon:
            trophy_x = self.DISPLAY_SIZE[0] // 2 - 200
            self.screen.blit(trophy_icon, (trophy_x, subtitle_y))
        
        subtitle_surface = self.font_large.render("Highest score gets a free tattoo!", True, self.retro.RETRO_COLORS['FIRE_RED'])
        subtitle_rect = subtitle_surface.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=subtitle_y)
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Instruction text
        instruction_y = subtitle_y + 60
        instruction_surface = self.font_medium.render("SCAN THE QR CODE TO ENTER THE BATTLE", True, self.retro.RETRO_COLORS['CYBER_GREEN'])
        instruction_rect = instruction_surface.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=instruction_y)
        self.screen.blit(instruction_surface, instruction_rect)

        # Left side - QR Code area
        qr_x = margin
        qr_y = header_height + margin
        qr_size = 300
        qr_box_width = qr_size + 80
        qr_box_height = qr_size + 100
        
        qr_box_rect = (qr_x, qr_y, qr_box_width, qr_box_height)
        self.draw_clean_overlay_box(qr_box_rect, alpha=220)
        
        # QR label with icon
        qr_icon = self.icons.get('qr')
        if qr_icon:
            self.screen.blit(qr_icon, (qr_x + 20, qr_y + 20))
        
        qr_label = self.font_small.render("SCAN TO PLAY", True, self.retro.RETRO_COLORS['CYBER_GREEN'])
        self.screen.blit(qr_label, (qr_x + 60, qr_y + 25))
        
        # Scale and display QR code
        qr_scaled = pygame.transform.scale(self.qr_image, (qr_size, qr_size))
        qr_display_x = qr_x + (qr_box_width - qr_size) // 2
        qr_display_y = qr_y + 60
        self.screen.blit(qr_scaled, (qr_display_x, qr_display_y))

        # Right side - High Scores area
        scores_x = qr_x + qr_box_width + margin
        scores_y = header_height + margin
        scores_w = self.DISPLAY_SIZE[0] - scores_x - margin
        scores_h = 500
        
        scores_box_rect = (scores_x, scores_y, scores_w, scores_h)
        self.draw_clean_overlay_box(scores_box_rect, alpha=220)
        
        # Scores header with icon
        star_icon = self.icons.get('star')
        if star_icon:
            self.screen.blit(star_icon, (scores_x + 20, scores_y + 20))
        
        scores_header = self.font_large.render("TOP WARRIORS", True, self.retro.RETRO_COLORS['TERMINAL_AMBER'])
        self.screen.blit(scores_header, (scores_x + 60, scores_y + 20))
        
        # Get and display scores
        scores = self.get_top_scores()
        y_offset = scores_y + 80
        
        if scores:
            for i, (name, score, timestamp, level) in enumerate(scores):
                if i >= 10:  # Limit to top 10
                    break
                    
                # Rank colors
                if i == 0:
                    color = self.retro.RETRO_COLORS['TERMINAL_AMBER']  # Gold
                    rank_icon = self.icons.get('trophy')
                elif i == 1:
                    color = self.retro.RETRO_COLORS['LIGHT_GRAY']  # Silver
                    rank_icon = self.icons.get('star')
                elif i == 2:
                    color = self.retro.RETRO_COLORS['FIRE_RED']  # Bronze
                    rank_icon = self.icons.get('gem')
                else:
                    color = self.retro.RETRO_COLORS['WHITE']
                    rank_icon = self.icons.get('heart')
                
                # Draw rank icon
                if rank_icon:
                    self.screen.blit(rank_icon, (scores_x + 20, y_offset + i * 35))
                
                # Format score line
                position = f"{i+1:2d}."
                display_name = name[:15] + "..." if len(name) > 15 else name
                score_text = f"{position} {display_name}: {score:,}"
                
                score_surface = self.font_small.render(score_text, True, color)
                self.screen.blit(score_surface, (scores_x + 60, y_offset + i * 35 + 5))
        else:
            # No scores message
            no_scores_surface = self.font_medium.render("NO SCORES YET - BE THE FIRST!", True, self.retro.RETRO_COLORS['HOT_MAGENTA'])
            no_scores_rect = no_scores_surface.get_rect(centerx=scores_x + scores_w//2, y=y_offset + 150)
            self.screen.blit(no_scores_surface, no_scores_rect)

        # Bottom status bar
        status_y = self.DISPLAY_SIZE[1] - 120
        status_rect = (0, status_y, self.DISPLAY_SIZE[0], 120)
        self.draw_clean_overlay_box(status_rect, alpha=240)
        
        # Left side status - Controller
        controller_icon = self.icons.get('controller')
        if controller_icon:
            self.screen.blit(controller_icon, (20, status_y + 20))
        
        controller_color = self.retro.RETRO_COLORS['LIME_SHOCK'] if self.controller_connected else self.retro.RETRO_COLORS['FIRE_RED']
        controller_text = "CONTROLLER: ONLINE" if self.controller_connected else "CONTROLLER: OFFLINE"
        controller_surface = self.font_tiny.render(controller_text, True, controller_color)
        self.screen.blit(controller_surface, (60, status_y + 30))
        
        # Center status - Game status
        if self.game_running and self.current_player:
            lightning_icon = self.icons.get('lightning')
            if lightning_icon:
                self.screen.blit(lightning_icon, (self.DISPLAY_SIZE[0] // 2 - 200, status_y + 20))
            
            game_text = f"NOW PLAYING: {self.current_player}"
            game_surface = self.font_small.render(game_text, True, self.retro.RETRO_COLORS['LIME_SHOCK'])
            game_rect = game_surface.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=status_y + 25)
            self.screen.blit(game_surface, game_rect)
        
        # Right side status - URL and instructions
        wifi_icon = self.icons.get('wifi')
        if wifi_icon:
            self.screen.blit(wifi_icon, (self.DISPLAY_SIZE[0] - 350, status_y + 20))
        
        url_text = f"FORM URL: {self.form_url}"
        url_surface = self.font_tiny.render(url_text, True, self.retro.RETRO_COLORS['ICE_BLUE'])
        self.screen.blit(url_surface, (self.DISPLAY_SIZE[0] - 320, status_y + 30))
        
        # Konami code hint
        konami_text = "KONAMI CODE FOR TEST MODE"
        konami_surface = self.font_tiny.render(konami_text, True, self.retro.RETRO_COLORS['PURPLE_HAZE'])
        self.screen.blit(konami_surface, (self.DISPLAY_SIZE[0] - 320, status_y + 60))
        
        # Update animation frame (for any remaining animations)
        self.retro.update_frame()

    def run(self):
        """Main kiosk loop"""
        logger.info("Starting retro kiosk main loop")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            while self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_F11:  # Toggle fullscreen
                            pygame.display.toggle_fullscreen()
                    elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION]:
                        self.handle_controller_input(event)

                # Reconnect controller if needed
                if not self.controller_connected:
                    current_time = time.time()
                    if current_time - self.last_check_time > 5:  # Check every 5 seconds
                        self.setup_controller()
                        self.last_check_time = current_time

                # Check for file triggers
                self.check_file_trigger()

                # Draw retro screen
                self.draw_retro_screen()

                # Update display
                pygame.display.flip()

                # Cap FPS to 30 for ARM processor
                self.clock.tick(30)

        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            self.cleanup()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up retro kiosk...")

        self.running = False

        # Stop MQTT client
        if self.mqtt_enabled and hasattr(self, 'mqtt_client'):
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except:
                pass

        # Stop game if running
        if self.game_process:
            try:
                self.game_process.terminate()
                self.game_process.wait(timeout=5)
            except:
                try:
                    self.game_process.kill()
                except:
                    pass

        # Close video capture
        if self.video_cap:
            try:
                self.video_cap.release()
            except:
                pass

        # Cleanup pygame
        pygame.quit()

        logger.info("Retro cleanup complete")

def main():
    """Main entry point"""
    try:
        kiosk = DoomBoxKiosk()
        kiosk.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
