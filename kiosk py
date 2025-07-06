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
import psutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import paho.mqtt.client as mqtt

class DoomBoxKiosk:
    def __init__(self):
        print("Initializing DoomBox Kiosk...")
        
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Display settings - Radxa Zero at 1280x960
        self.DISPLAY_SIZE = (1280, 960)
        self.screen = pygame.display.set_mode(self.DISPLAY_SIZE, pygame.FULLSCREEN)
        pygame.display.set_caption("shmegl's DoomBox")
        pygame.mouse.set_visible(False)  # Hide mouse cursor
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
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
        
        # Controller
        self.controller = None
        self.setup_controller()
        
        # Konami code for DualShock 4 (using button indices)
        # UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, X, O
        self.konami_sequence = [
            'dpad_up', 'dpad_up', 'dpad_down', 'dpad_down',
            'dpad_left', 'dpad_right', 'dpad_left', 'dpad_right',
            'button_0', 'button_1'  # X, Circle on DS4
        ]
        self.konami_input = []
        self.konami_timeout = 5.0  # Reset sequence after 5 seconds
        self.last_konami_input = time.time()
        
        # Configuration
        self.form_url = "https://your-username.github.io/doombox-form/"
        self.mqtt_enabled = True
        
        # Initialize database
        self.init_database()
        
        # Generate QR code
        self.qr_image = self.generate_qr_code()
        
        # Start MQTT listener
        if self.mqtt_enabled:
            self.setup_mqtt()
        
        # Fonts
        self.setup_fonts()
        
        print("DoomBox Kiosk initialized successfully!")

    def setup_fonts(self):
        """Initialize pygame fonts"""
        try:
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            self.font_tiny = pygame.font.Font(None, 24)
        except:
            # Fallback to default font
            self.font_large = pygame.font.SysFont('arial', 72)
            self.font_medium = pygame.font.SysFont('arial', 48)
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
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((250, 250))
            
            # Convert PIL image to pygame surface
            qr_surface = pygame.image.fromstring(qr_img.tobytes(), qr_img.size, qr_img.mode)
            print("QR code generated successfully")
            return qr_surface
        except Exception as e:
            print(f"QR code generation error: {e}")
            # Create placeholder surface
            surface = pygame.Surface((250, 250))
            surface.fill(self.WHITE)
            pygame.draw.rect(surface, self.BLACK, (10, 10, 230, 230), 5)
            return surface

    def setup_mqtt(self):
        """Setup MQTT client for remote game triggers"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            # Connect to local mosquitto broker
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            print("MQTT client setup successful")
        except Exception as e:
            print(f"MQTT setup failed: {e}")
            self.mqtt_enabled = False

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print("MQTT connected successfully")
            client.subscribe("doombox/start_game")
        else:
            print(f"MQTT connection failed with code {rc}")

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
        
        # Center title elements
        title_x = self.DISPLAY_SIZE[0] // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, 30))
        
        subtitle_x = self.DISPLAY_SIZE[0] // 2 - subtitle.get_width() // 2
        self.screen.blit(subtitle, (subtitle_x, 100))
        
        instruction_x = self.DISPLAY_SIZE[0] // 2 - instruction.get_width() // 2
        self.screen.blit(instruction, (instruction_x, 150))
        
        # QR Code (left side)
        qr_x = 100
        qr_y = 220
        self.screen.blit(self.qr_image, (qr_x, qr_y))
        
        # QR Code label
        qr_label = self.font_small.render("Scan to Play", True, self.WHITE)
        qr_label_x = qr_x + 125 - qr_label.get_width() // 2
        self.screen.blit(qr_label, (qr_label_x, qr_y + 260))
        
        # Top scores (right side)
        scores_x = 450
        scores_y = 220
        
        scores_title = self.font_medium.render("TOP SCORES", True, self.YELLOW)
        self.screen.blit(scores_title, (scores_x, scores_y))
        
        scores = self.get_top_scores()
        y_offset = scores_y + 50
        
        if scores:
            for i, (name, score, timestamp, level) in enumerate(scores):
                if i == 0:
                    color = self.YELLOW  # Gold for first place
                elif i == 1:
                    color = self.WHITE   # Silver for second
                elif i == 2:
                    color = self.GRAY    # Bronze for third
                else:
                    color = self.WHITE
                
                # Truncate long names
                display_name = name[:15] + "..." if len(name) > 15 else name
                score_text = self.font_small.render(f"{i+1:2d}. {display_name}: {score:,}", True, color)
                self.screen.blit(score_text, (scores_x, y_offset + i * 35))
        else:
            no_scores = self.font_small.render("No scores yet!", True, self.GRAY)
            self.screen.blit(no_scores, (scores_x, y_offset))
        
        # Game status
        status_y = 750
        if self.game_running and self.current_player:
            status_text = self.font_medium.render(f"NOW PLAYING: {self.current_player}", True, self.GREEN)
            status_x = self.DISPLAY_SIZE[0] // 2 - status_text.get_width() // 2
            self.screen.blit(status_text, (status_x, status_y))
        
        # Controller status
        controller_status = "Controller: Connected" if self.controller else "Controller: Not Found"
        controller_color = self.GREEN if self.controller else self.RED
        controller_text = self.font_tiny.render(controller_status, True, controller_color)
        self.screen.blit(controller_text, (10, self.DISPLAY_SIZE[1] - 50))
        
        # Konami code hint
        hint_text = self.font_tiny.render("Konami Code for Test Mode", True, self.GRAY)
        hint_x = self.DISPLAY_SIZE[0] - hint_text.get_width() - 10
        self.screen.blit(hint_text, (hint_x, self.DISPLAY_SIZE[1] - 50))
        
        # Version info
        version_text = self.font_tiny.render("DoomBox v1.0", True, self.GRAY)
        self.screen.blit(version_text, (10, 10))
        
        pygame.display.flip()

    def handle_controller_input(self):
        """Handle controller input including Konami code"""
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
        # DualShock 4 button mapping
        button_map = {
            0: 'button_0',  # X
            1: 'button_1',  # Circle
            2: 'button_2',  # Square
            3: 'button_3',  # Triangle
        }
        
        if button in button_map:
            self.check_konami_input(button_map[button])

    def handle_joystick_hat(self, hat_value):
        """Handle D-pad input (hat)"""
        # D-pad mappings
        hat_map = {
            (0, 1): 'dpad_up',
            (0, -1): 'dpad_down',
            (-1, 0): 'dpad_left',
            (1, 0): 'dpad_right',
        }
        
        if hat_value in hat_map:
            self.check_konami_input(hat_map[hat_value])

    def check_konami_input(self, input_type):
        """Check if input matches Konami sequence"""
        current_time = time.time()
        
        # Reset sequence if too much time has passed
        if current_time - self.last_konami_input > self.konami_timeout:
            self.konami_input = []
        
        self.last_konami_input = current_time
        self.konami_input.append(input_type)
        
        # Keep only the last N inputs where N is sequence length
        if len(self.konami_input) > len(self.konami_sequence):
            self.konami_input.pop(0)
        
        # Check if sequence matches
        if self.konami_input == self.konami_sequence:
            print("Konami code activated! Starting test game...")
            self.start_game("TEST_PLAYER")
            self.konami_input = []

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
        start_time = time.time()
        try:
            # DOOM command using the compatibility wrapper
            doom_cmd = [
                '/usr/local/bin/lzdoom',
                '-iwad', f'{self.doom_dir}/DOOM.WAD',
                '-width', '640',
                '-height', '480',
                '-fullscreen',
                '+name', player_name
            ]
            
            print(f"Launching DOOM: {' '.join(doom_cmd)}")
            
            # Log command to file
            with open(f"{self.logs_dir}/doom.log", "a") as log_file:
                log_file.write(f"{datetime.now()}: Starting DOOM for {player_name}\n")
                log_file.write(f"Command: {' '.join(doom_cmd)}\n")
            
            # Run DOOM
            self.game_process = subprocess.Popen(
                doom_cmd, 
                cwd=self.doom_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for game to finish
            stdout, stderr = self.game_process.communicate()
            
            # Calculate play time
            play_time = int(time.time() - start_time)
            
            # Game ended, extract score (simplified)
            score = self._extract_score(stdout, stderr)
            
            # Don't save test scores
            if not player_name.startswith("TEST_"):
                self.add_score(player_name, score, time_played=play_time)
            
            print(f"Game ended. Score: {score}, Play time: {play_time}s")
            
            # Log results
            with open(f"{self.logs_dir}/doom.log", "a") as log_file:
                log_file.write(f"{datetime.now()}: Game ended - Score: {score}, Time: {play_time}s\n")
            
        except Exception as e:
            print(f"Error running DOOM: {e}")
            with open(f"{self.logs_dir}/doom.log", "a") as log_file:
                log_file.write(f"{datetime.now()}: ERROR - {e}\n")
        finally:
            self.game_running = False
            self.current_player = None
            self.game_process = None

    def _extract_score(self, stdout, stderr):
        """Extract score from DOOM output (simplified implementation)"""
        # This is a placeholder implementation
        # In reality, you'd need to:
        # 1. Parse DOOM's save files or demo files
        # 2. Use DOOM's built-in demo recording
        # 3. Implement a custom DOOM mod that outputs scores
        # 4. Parse stdout/stderr for score information
        
        import random
        base_score = random.randint(1000, 50000)
        
        # Add some variability based on play time if available
        try:
            if stdout:
                # Look for any numbers that might be scores
                import re
                numbers = re.findall(r'\b\d+\b', stdout.decode('utf-8', errors='ignore'))
                if numbers:
                    # Use the largest number found as a potential score
                    potential_score = max(int(n) for n in numbers if int(n) > 100)
                    if potential_score > base_score:
                        base_score = potential_score
        except:
            pass
        
        return base_score

    def check_for_new_players(self):
        """Check for new players via webhook/API/file"""
        current_time = time.time()
        
        # Only check every 2 seconds to avoid excessive file I/O
        if current_time - self.last_check_time < 2.0:
            return
        
        self.last_check_time = current_time
        
        try:
            # Check for trigger file from webhook
            trigger_file = f"{self.base_dir}/new_player.json"
            if os.path.exists(trigger_file):
                with open(trigger_file, 'r') as f:
                    data = json.load(f)
                
                player_name = data.get('player_name', 'Unknown')
                print(f"New player from file: {player_name}")
                self.start_game(player_name)
                
                # Remove trigger file
                os.remove(trigger_file)
                
            # Also check for API endpoint (if implemented)
            # This would be a simple HTTP check to your GitHub Pages site
            
        except Exception as e:
            # Don't spam console with errors
            pass

    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up DoomBox resources...")
        
        # Stop MQTT client
        if hasattr(self, 'mqtt_client') and self.mqtt_enabled:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except:
                pass
        
        # Kill any running DOOM process
        if self.gam
