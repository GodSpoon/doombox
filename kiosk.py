#!/usr/bin/env python3
"""
shmegl's DoomBox Kiosk Application - Fixed and Optimized
Simplified for reliable operation on Radxa Zero
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
from datetime import datetime
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: MQTT not available")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/doombox/logs/kiosk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DoomBoxKiosk:
    def __init__(self):
        logger.info("Initializing DoomBox Kiosk...")
        
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
        
        pygame.display.set_caption("shmegl's DoomBox")
        pygame.mouse.set_visible(False)
        
        # Color palette - simplified for better performance
        self.COLORS = {
            'BLACK': (0, 0, 0),
            'WHITE': (255, 255, 255),
            'RED': (255, 0, 0),
            'GREEN': (0, 255, 0),
            'BLUE': (0, 0, 255),
            'YELLOW': (255, 255, 0),
            'CYAN': (0, 255, 255),
            'MAGENTA': (255, 0, 255),
            'GRAY': (128, 128, 128),
            'DARK_GRAY': (64, 64, 64),
            'ORANGE': (255, 165, 0),
            'PURPLE': (128, 0, 128)
        }
        
        # Animation variables
        self.frame_count = 0
        self.title_pulse = 0
        
        # Paths
        self.base_dir = "/opt/doombox"
        self.doom_dir = f"{self.base_dir}/doom"
        self.db_path = f"{self.base_dir}/scores.db"
        self.logs_dir = f"{self.base_dir}/logs"
        self.trigger_file = f"{self.base_dir}/new_player.json"
        
        # Ensure directories exist
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Game state
        self.current_player = None
        self.game_running = False
        self.game_process = None
        self.last_check_time = time.time()
        self.running = True
        
        # Controller
        self.controller = None
        self.controller_connected = False
        self.setup_controller()
        
        # Konami sequence for test mode
        self.konami_sequence = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
        self.konami_input = []
        self.konami_timeout = 5.0
        self.last_konami_input = time.time()
        
        # Configuration
        self.form_url = "http://shmeglsdoombox.spoon.rip"
        self.mqtt_enabled = MQTT_AVAILABLE
        
        # Initialize components
        self.init_database()
        self.qr_image = self.generate_qr_code()
        self.setup_fonts()
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        
        # Setup MQTT if available
        if self.mqtt_enabled:
            self.setup_mqtt()
        
        # Start file monitoring thread
        self.start_file_monitor()
        
        logger.info("DoomBox Kiosk initialized successfully!")

    def setup_fonts(self):
        """Initialize fonts optimized for ARM processor"""
        try:
            # Use system fonts for better performance on ARM
            self.font_huge = pygame.font.Font(None, 96)      # Title
            self.font_large = pygame.font.Font(None, 64)     # Subtitle  
            self.font_medium = pygame.font.Font(None, 48)    # Headers
            self.font_small = pygame.font.Font(None, 32)     # Content
            self.font_tiny = pygame.font.Font(None, 24)      # Footer
            logger.info("Fonts initialized successfully")
        except Exception as e:
            logger.error(f"Font setup error: {e}")
            # Fallback fonts
            self.font_huge = pygame.font.SysFont('monospace', 96, bold=True)
            self.font_large = pygame.font.SysFont('monospace', 64, bold=True)
            self.font_medium = pygame.font.SysFont('monospace', 48, bold=True)
            self.font_small = pygame.font.SysFont('monospace', 32)
            self.font_tiny = pygame.font.SysFont('monospace', 24)

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

    def generate_qr_code(self):
        """Generate QR code for the registration form"""
        try:
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(self.form_url)
            qr.make(fit=True)
            
            # Create QR image
            qr_img = qr.make_image(fill_color='white', back_color='black')
            qr_img = qr_img.resize((300, 300))
            
            # Convert to pygame surface
            mode = qr_img.mode
            size = qr_img.size
            data = qr_img.tobytes()
            qr_surface = pygame.image.fromstring(data, size, mode)
            
            logger.info("QR code generated successfully")
            return qr_surface
            
        except Exception as e:
            logger.error(f"QR code generation error: {e}")
            # Create fallback QR placeholder
            surface = pygame.Surface((300, 300))
            surface.fill(self.COLORS['GRAY'])
            
            # Draw placeholder text
            error_text = self.font_medium.render("QR ERROR", True, self.COLORS['RED'])
            text_rect = error_text.get_rect(center=(150, 150))
            surface.blit(error_text, text_rect)
            
            return surface

    def setup_mqtt(self):
        """Setup MQTT client"""
        if not MQTT_AVAILABLE:
            return
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            logger.info("MQTT client setup successful")
        except Exception as e:
            logger.error(f"MQTT setup failed: {e}")
            self.mqtt_enabled = False

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected successfully")
            client.subscribe("doombox/start_game")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            player_name = data.get('player_name', 'Unknown')
            logger.info(f"MQTT: Starting game for {player_name}")
            self.start_game(player_name)
        except Exception as e:
            logger.error(f"MQTT message error: {e}")

    def start_file_monitor(self):
        """Start file monitoring thread"""
        def monitor_files():
            while self.running:
                try:
                    if os.path.exists(self.trigger_file):
                        with open(self.trigger_file, 'r') as f:
                            data = json.load(f)
                        
                        player_name = data.get('player_name', 'Unknown')
                        logger.info(f"File trigger: Starting game for {player_name}")
                        
                        # Remove trigger file
                        os.remove(self.trigger_file)
                        
                        # Start game
                        self.start_game(player_name)
                    
                    time.sleep(1)  # Check every second
                except Exception as e:
                    logger.error(f"File monitor error: {e}")
                    time.sleep(5)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_files, daemon=True)
        monitor_thread.start()
        logger.info("File monitor started")

    def setup_controller(self):
        """Setup DualShock 4 controller"""
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            
            joystick_count = pygame.joystick.get_count()
            logger.info(f"Found {joystick_count} controller(s)")
            
            if joystick_count > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                controller_name = self.controller.get_name()
                self.controller_connected = True
                logger.info(f"Controller connected: {controller_name}")
                return True
            else:
                self.controller_connected = False
                logger.warning("No controller found")
                return False
        except Exception as e:
            logger.error(f"Controller setup error: {e}")
            self.controller_connected = False
            return False

    def check_konami_code(self, input_name):
        """Check if konami code is being entered"""
        current_time = time.time()
        
        # Reset if timeout
        if current_time - self.last_konami_input > self.konami_timeout:
            self.konami_input = []
        
        self.last_konami_input = current_time
        self.konami_input.append(input_name)
        
        # Keep only last 10 inputs
        if len(self.konami_input) > 10:
            self.konami_input = self.konami_input[-10:]
        
        # Check if sequence matches
        if len(self.konami_input) >= len(self.konami_sequence):
            recent_inputs = self.konami_input[-len(self.konami_sequence):]
            if recent_inputs == self.konami_sequence:
                logger.info("Konami code activated!")
                self.konami_input = []  # Reset
                self.start_test_game()
                return True
        
        return False

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
            logger.error(f"Error getting scores: {e}")
            return []

    def add_score(self, player_name, score, level=1, time_played=0):
        """Add score to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scores (player_name, score, timestamp, level_reached, time_played)
                VALUES (?, ?, ?, ?, ?)
            ''', (player_name, score, datetime.now(), level, time_played))
            conn.commit()
            conn.close()
            logger.info(f"Score added: {player_name} - {score} points")
        except Exception as e:
            logger.error(f"Error adding score: {e}")

    def start_game(self, player_name):
        """Start DOOM game for player"""
        if self.game_running:
            logger.warning("Game already running, ignoring start request")
            return
        
        try:
            self.current_player = player_name
            self.game_running = True
            
            logger.info(f"Starting DOOM for player: {player_name}")
            
            # DOOM command
            doom_cmd = [
                "/usr/local/bin/lzdoom",  # Our compatibility wrapper
                "-iwad", f"{self.doom_dir}/DOOM.WAD",
                "-width", "640",
                "-height", "480", 
                "-fullscreen",
                "+name", player_name
            ]
            
            # Start DOOM process
            self.game_process = subprocess.Popen(
                doom_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, DISPLAY=":0")
            )
            
            logger.info(f"DOOM started with PID: {self.game_process.pid}")
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_game, daemon=True)
            monitor_thread.start()
            
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
            # Wait for game to finish
            return_code = self.game_process.wait()
            logger.info(f"DOOM exited with code: {return_code}")
            
            # Parse score (simplified - in real implementation, read from DOOM output)
            # For now, generate a random score for testing
            import random
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

    def draw_screen(self):
        """Draw the main kiosk screen"""
        # Clear screen
        self.screen.fill(self.COLORS['BLACK'])
        
        # Title with pulse effect
        pulse = math.sin(self.frame_count * 0.05) * 0.3 + 1.0
        title_color = tuple(int(c * pulse) for c in self.COLORS['RED'])
        title_color = tuple(min(255, max(50, c)) for c in title_color)
        
        title = self.font_huge.render("shmegl's DoomBox", True, title_color)
        title_rect = title.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=50)
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_large.render("Highest score gets a free tattoo!", True, self.COLORS['YELLOW'])
        subtitle_rect = subtitle.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=150)
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instruction
        instruction = self.font_medium.render("SCAN THE QR CODE TO ENTER THE BATTLE", True, self.COLORS['GREEN'])
        instruction_rect = instruction.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=220)
        self.screen.blit(instruction, instruction_rect)
        
        # QR Code
        qr_x = 150
        qr_y = 300
        self.screen.blit(self.qr_image, (qr_x, qr_y))
        
        # QR Label
        qr_label = self.font_small.render(">> SCAN TO PLAY <<", True, self.COLORS['CYAN'])
        qr_label_rect = qr_label.get_rect(centerx=qr_x + 150, y=qr_y + 320)
        self.screen.blit(qr_label, qr_label_rect)
        
        # High Scores
        scores_x = 550
        scores_y = 300
        
        # Scores header
        scores_header = self.font_medium.render("TOP WARRIORS", True, self.COLORS['WHITE'])
        self.screen.blit(scores_header, (scores_x, scores_y))
        
        # Get and display scores
        scores = self.get_top_scores()
        y_offset = scores_y + 50
        
        if scores:
            for i, (name, score, timestamp, level) in enumerate(scores):
                # Different colors for top 3
                if i == 0:
                    color = self.COLORS['YELLOW']  # Gold
                elif i == 1:
                    color = self.COLORS['GRAY']    # Silver
                elif i == 2:
                    color = self.COLORS['ORANGE']  # Bronze
                else:
                    color = self.COLORS['WHITE']
                
                # Format score line
                position = f"{i+1:2d}."
                display_name = name[:15] + "..." if len(name) > 15 else name
                score_text = f"{position} {display_name}: {score:,}"
                
                score_surface = self.font_small.render(score_text, True, color)
                self.screen.blit(score_surface, (scores_x, y_offset + i * 35))
        else:
            no_scores = self.font_small.render("NO SCORES YET - BE THE FIRST!", True, self.COLORS['GRAY'])
            self.screen.blit(no_scores, (scores_x, y_offset + 100))
        
        # Status indicators
        status_y = self.DISPLAY_SIZE[1] - 80
        
        # Controller status
        controller_color = self.COLORS['GREEN'] if self.controller_connected else self.COLORS['RED']
        controller_text = "CONTROLLER: CONNECTED" if self.controller_connected else "CONTROLLER: DISCONNECTED"
        controller_surface = self.font_tiny.render(controller_text, True, controller_color)
        self.screen.blit(controller_surface, (20, status_y))
        
        # Game status
        if self.game_running and self.current_player:
            game_text = f"NOW PLAYING: {self.current_player}"
            game_surface = self.font_tiny.render(game_text, True, self.COLORS['CYAN'])
            self.screen.blit(game_surface, (20, status_y + 25))
        
        # URL display
        url_text = f"Form URL: {self.form_url}"
        url_surface = self.font_tiny.render(url_text, True, self.COLORS['GRAY'])
        url_rect = url_surface.get_rect(right=self.DISPLAY_SIZE[0] - 20, y=status_y)
        self.screen.blit(url_surface, url_rect)
        
        # Konami code hint
        hint_text = "KONAMI CODE FOR TEST MODE"
        hint_surface = self.font_tiny.render(hint_text, True, self.COLORS['GRAY'])
        hint_rect = hint_surface.get_rect(right=self.DISPLAY_SIZE[0] - 20, y=status_y + 25)
        self.screen.blit(hint_surface, hint_rect)

    def run(self):
        """Main kiosk loop"""
        logger.info("Starting kiosk main loop")
        
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
                
                # Draw screen
                self.draw_screen()
                
                # Update display
                pygame.display.flip()
                
                # Update frame counter
                self.frame_count += 1
                
                # Cap FPS
                self.clock.tick(30)  # 30 FPS for ARM processor
                
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
        logger.info("Cleaning up...")
        
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
        
        # Cleanup pygame
        pygame.quit()
        
        logger.info("Cleanup complete")

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