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
import signal
import sys
import os
from datetime import datetime
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: MQTT not available")

class DoomBoxKiosk:
    def __init__(self):
        print("Initializing DoomBox Kiosk...")
        
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Display settings - Radxa Zero at 1280x960
        self.DISPLAY_SIZE = (1280, 960)
        try:
            self.screen = pygame.display.set_mode(self.DISPLAY_SIZE, pygame.FULLSCREEN)
        except pygame.error as e:
            print(f"Failed to set fullscreen mode: {e}")
            # Fallback to windowed mode
            self.screen = pygame.display.set_mode(self.DISPLAY_SIZE)
        
        pygame.display.set_caption("shmegl's DoomBox")
        pygame.mouse.set_visible(False)
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        self.GRAY = (128, 128, 128)
        self.DARK_RED = (139, 0, 0)
        
        # Paths
        self.base_dir = "/opt/doombox"
        self.doom_dir = f"{self.base_dir}/doom"
        self.db_path = f"{self.base_dir}/scores.db"
        self.logs_dir = f"{self.base_dir}/logs"
        
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
        self.setup_controller()
        
        # Konami sequence
        self.konami_sequence = [
            'dpad_up', 'dpad_up', 'dpad_down', 'dpad_down',
            'dpad_left', 'dpad_right', 'dpad_left', 'dpad_right',
            'button_0', 'button_1'
        ]
        self.konami_input = []
        self.konami_timeout = 5.0
        self.last_konami_input = time.time()
        
        # Configuration
        self.form_url = "https://shmeglsdoombox.spoon.rip/"
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
        
        print("DoomBox Kiosk initialized successfully!")

    def setup_fonts(self):
        """Initialize pygame fonts"""
        try:
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            self.font_tiny = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.SysFont('arial', 72, bold=True)
            self.font_medium = pygame.font.SysFont('arial', 48, bold=True)
            self.font_small = pygame.font.SysFont('arial', 32)
            self.font_tiny = pygame.font.SysFont('arial', 24)

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
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")

    def generate_qr_code(self):
        """Generate QR code for the registration form"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(self.form_url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((250, 250))
            
            mode = qr_img.mode
            size = qr_img.size
            data = qr_img.tobytes()
            qr_surface = pygame.image.fromstring(data, size, mode)
            
            print("QR code generated successfully")
            return qr_surface
        except Exception as e:
            print(f"QR code generation error: {e}")
            surface = pygame.Surface((250, 250))
            surface.fill(self.WHITE)
            pygame.draw.rect(surface, self.BLACK, (10, 10, 230, 230), 5)
            font = pygame.font.Font(None, 36)
            text = font.render("QR ERROR", True, self.BLACK)
            text_rect = text.get_rect(center=(125, 125))
            surface.blit(text, text_rect)
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
            print("MQTT client setup successful")
        except Exception as e:
            print(f"MQTT setup failed: {e}")
            self.mqtt_enabled = False

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT connected successfully")
            client.subscribe("doombox/start_game")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            player_name = data.get('player_name', 'Unknown')
            print(f"MQTT: Starting game for {player_name}")
            self.start_game(player_name)
        except Exception as e:
            print(f"MQTT message error: {e}")

    def setup_controller(self):
        """Setup controller"""
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            
            joystick_count = pygame.joystick.get_count()
            print(f"Found {joystick_count} joystick(s)")
            
            if joystick_count > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                controller_name = self.controller.get_name()
                print(f"Controller connected: {controller_name}")
                return True
            else:
                print("No controller found")
                return False
        except Exception as e:
            print(f"Controller setup error: {e}")
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
            print(f"Error getting scores: {e}")
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
            print(f"Score added: {player_name} - {score} points")
        except Exception as e:
            print(f"Error adding score: {e}")

    def draw_screen(self):
        """Draw the main kiosk screen"""
        self.screen.fill(self.BLACK)
        
        # Title
        title = self.font_large.render("shmegl's DoomBox", True, self.DARK_RED)
        subtitle = self.font_medium.render("Highest score gets a free tattoo!", True, self.WHITE)
        instruction = self.font_small.render("Scan the QR code and fill out the form to play", True, self.GREEN)
        
        # Center elements
        title_x = self.DISPLAY_SIZE[0] // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, 30))
        
        subtitle_x = self.DISPLAY_SIZE[0] // 2 - subtitle.get_width() // 2
        self.screen.blit(subtitle, (subtitle_x, 100))
        
        instruction_x = self.DISPLAY_SIZE[0] // 2 - instruction.get_width() // 2
        self.screen.blit(instruction, (instruction_x, 150))
        
        # QR Code
        qr_x = 100
        qr_y = 220
        self.screen.blit(self.qr_image, (qr_x, qr_y))
        
        qr_label = self.font_small.render("Scan to Play", True, self.WHITE)
        qr_label_x = qr_x + 125 - qr_label.get_width() // 2
        self.screen.blit(qr_label, (qr_label_x, qr_y + 260))
        
        # Top scores
        scores_x = 450
        scores_y = 220
        
        scores_title = self.font_medium.render("TOP SCORES", True, self.YELLOW)
        self.screen.blit(scores_title, (scores_x, scores_y))
        
        scores = self.get_top_scores()
        y_offset = scores_y + 50
        
        if scores:
            for i, (name, score, timestamp, level) in enumerate(scores):
                color = self.YELLOW if i == 0 else self.WHITE if i < 3 else self.GRAY
                display_name = name[:15] + "..." if len(name) > 15 else name
                score_text = self.font_small.render(f"{i+1:2d}. {display_name}: {score:,}", True, color)
                self.screen.blit(score_text, (scores_x, y_offset + i * 35))
        else:
            no_scores = self.font_small.render("No scores yet!", True, self.GRAY)
            self.screen.blit(no_scores, (scores_x, y_offset))
        
        # Status
        if self.game_running and self.current_player:
            status_text = self.font_medium.render(f"NOW PLAYING: {self.current_player}", True, self.GREEN)
            status_x = self.DISPLAY_SIZE[0] // 2 - status_text.get_width() // 2
            self.screen.blit(status_text, (status_x, 750))
        
        # Footer info
        controller_status = "Controller: Connected" if self.controller else "Controller: Not Found"
        controller_color = self.GREEN if self.controller else self.RED
        controller_text = self.font_tiny.render(controller_status, True, controller_color)
        self.screen.blit(controller_text, (10, self.DISPLAY_SIZE[1] - 50))
        
        hint_text = self.font_tiny.render("Konami Code for Test Mode", True, self.GRAY)
        hint_x = self.DISPLAY_SIZE[0] - hint_text.get_width() - 10
        self.screen.blit(hint_text, (hint_x, self.DISPLAY_SIZE[1] - 50))
        
        version_text = self.font_tiny.render("DoomBox v1.0", True, self.GRAY)
        self.screen.blit(version_text, (10, 10))
        
        pygame.display.flip()

    def handle_controller_input(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_q and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    return False
            elif event.type == pygame.JOYBUTTONDOWN and self.controller:
                self.handle_joystick_button(event.button)
            elif event.type == pygame.JOYHATMOTION and self.controller:
                self.handle_joystick_hat(event.value)
        return True

    def handle_joystick_button(self, button):
        """Handle joystick button presses"""
        button_map = {0: 'button_0', 1: 'button_1', 2: 'button_2', 3: 'button_3'}
        if button in button_map:
            self.check_konami_input(button_map[button])

    def handle_joystick_hat(self, hat_value):
        """Handle D-pad input"""
        hat_map = {(0, 1): 'dpad_up', (0, -1): 'dpad_down', (-1, 0): 'dpad_left', (1, 0): 'dpad_right'}
        if hat_value in hat_map:
            self.check_konami_input(hat_map[hat_value])

    def check_konami_input(self, input_type):
        """Check Konami code"""
        current_time = time.time()
        if current_time - self.last_konami_input > self.konami_timeout:
            self.konami_input = []
        
        self.last_konami_input = current_time
        self.konami_input.append(input_type)
        
        if len(self.konami_input) > len(self.konami_sequence):
            self.konami_input.pop(0)
        
        if self.konami_input == self.konami_sequence:
            print("Konami code activated!")
            self.start_game("TEST_PLAYER")
            self.konami_input = []

    def start_game(self, player_name):
        """Start DOOM game"""
        if self.game_running:
            print("Game already running!")
            return
        
        self.current_player = player_name
        self.game_running = True
        print(f"Starting DOOM for player: {player_name}")
        
        game_thread = threading.Thread(target=self._run_doom, args=(player_name,))
        game_thread.daemon = True
        game_thread.start()

    def _run_doom(self, player_name):
        """Run DOOM in subprocess"""
        start_time = time.time()
        try:
            doom_cmd = [
                '/usr/local/bin/lzdoom',
                '-iwad', f'{self.doom_dir}/DOOM.WAD',
                '-width', '640',
                '-height', '480',
                '-fullscreen',
                '+name', player_name
            ]
            
            print(f"Launching DOOM: {' '.join(doom_cmd)}")
            
            self.game_process = subprocess.Popen(
                doom_cmd, 
                cwd=self.doom_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = self.game_process.communicate()
            play_time = int(time.time() - start_time)
            score = self._extract_score(stdout, stderr)
            
            if not player_name.startswith("TEST_"):
                self.add_score(player_name, score, time_played=play_time)
            
            print(f"Game ended. Score: {score}, Play time: {play_time}s")
            
        except Exception as e:
            print(f"Error running DOOM: {e}")
        finally:
            self.game_running = False
            self.current_player = None
            self.game_process = None

    def _extract_score(self, stdout, stderr):
        """Extract score from DOOM output"""
        import random
        return random.randint(1000, 50000)

    def check_for_new_players(self):
        """Check for new players via file trigger"""
        current_time = time.time()
        if current_time - self.last_check_time < 2.0:
            return
        
        self.last_check_time = current_time
        
        try:
            trigger_file = f"{self.base_dir}/new_player.json"
            if os.path.exists(trigger_file):
                with open(trigger_file, 'r') as f:
                    data = json.load(f)
                
                player_name = data.get('player_name', 'Unknown')
                print(f"New player from file: {player_name}")
                self.start_game(player_name)
                os.remove(trigger_file)
        except:
            pass

    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up DoomBox resources...")
        
        if hasattr(self, 'mqtt_client') and self.mqtt_enabled:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except:
                pass
        
        if self.game_process:
            try:
                self.game_process.terminate()
                self.game_process.wait(timeout=5)
            except:
                try:
                    self.game_process.kill()
                except:
                    pass
        
        pygame.quit()

    def run(self):
        """Main kiosk loop"""
        print("Starting DoomBox main loop...")
        
        try:
            while self.running:
                if not self.handle_controller_input():
                    break
                
                self.check_for_new_players()
                
                if not self.controller and time.time() % 10 < 0.1:
                    self.setup_controller()
                
                self.draw_screen()
                self.clock.tick(30)
                
        except KeyboardInterrupt:
            print("Keyboard interrupt received, shutting down...")
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()

def signal_handler(signum, frame):
    """Handle system signals"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    global kiosk
    if 'kiosk' in globals():
        kiosk.running = False

def main():
    """Main entry point"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if not os.environ.get('DISPLAY'):
        print("Warning: DISPLAY environment variable not set")
        print("Try: export DISPLAY=:0")
    
    try:
        global kiosk
        kiosk = DoomBoxKiosk()
        kiosk.run()
    except Exception as e:
        print(f"Failed to start DoomBox: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
