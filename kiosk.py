#!/usr/bin/env python3
"""
shmegl's DoomBox Kiosk Application - Retro Edition
Enhanced with authentic retro aesthetics and CRT-style visuals
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
from datetime import datetime
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: MQTT not available")

class RetroFont:
    """Custom retro bitmap font renderer"""
    def __init__(self):
        # Simple 8x8 pixel font patterns for retro feel
        self.char_width = 8
        self.char_height = 8
        
    def render_text(self, surface, text, x, y, color, scale=1):
        """Render text with pixelated font"""
        for i, char in enumerate(text.upper()):
            char_x = x + (i * self.char_width * scale)
            if char == ' ':
                continue
            # For simplicity, use pygame's font but with crisp rendering
            font = pygame.font.Font(None, int(self.char_height * scale * 2))
            text_surface = font.render(char, False, color)
            # Scale up for pixelated effect
            if scale > 1:
                w, h = text_surface.get_size()
                text_surface = pygame.transform.scale(text_surface, (w * scale, h * scale))
            surface.blit(text_surface, (char_x, y))

class RetroEffects:
    """Retro visual effects for CRT/arcade feel"""
    
    @staticmethod
    def add_scanlines(surface, intensity=0.1):
        """Add horizontal scanlines for CRT effect"""
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(int(255 * intensity))
        
        for y in range(0, surface.get_height(), 2):
            pygame.draw.line(overlay, (0, 0, 0), (0, y), (surface.get_width(), y))
        
        surface.blit(overlay, (0, 0))
    
    @staticmethod
    def add_glow(surface, color, radius=3):
        """Add glow effect to surface"""
        mask = pygame.mask.from_surface(surface)
        glow_surface = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
        
        # Create glow by blitting multiple slightly offset copies
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    surface.blit(glow_surface, (dx, dy), special_flags=pygame.BLEND_ADD)
    
    @staticmethod
    def create_border_frame(surface, thickness=4, colors=None):
        """Create retro-style border frame"""
        if colors is None:
            colors = [(255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255)]
        
        width, height = surface.get_size()
        
        # Outer frame
        for i in range(thickness):
            color = colors[i % len(colors)]
            pygame.draw.rect(surface, color, 
                           (i, i, width - 2*i, height - 2*i), 1)

class DoomBoxKiosk:
    def __init__(self):
        print("Initializing Enhanced Retro DoomBox Kiosk...")
        
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Display settings - Enhanced for retro feel
        self.DISPLAY_SIZE = (1280, 960)
        try:
            self.screen = pygame.display.set_mode(self.DISPLAY_SIZE, pygame.FULLSCREEN)
        except pygame.error as e:
            print(f"Failed to set fullscreen mode: {e}")
            self.screen = pygame.display.set_mode(self.DISPLAY_SIZE)
        
        pygame.display.set_caption("shmegl's DoomBox - Retro Edition")
        pygame.mouse.set_visible(False)
        
        # Retro color palette (inspired by classic arcade machines)
        self.RETRO_COLORS = {
            'BLACK': (0, 0, 0),
            'DARK_GRAY': (32, 32, 32),
            'GRAY': (64, 64, 64),
            'LIGHT_GRAY': (128, 128, 128),
            'WHITE': (255, 255, 255),
            'BRIGHT_RED': (255, 0, 0),
            'DARK_RED': (128, 0, 0),
            'BRIGHT_GREEN': (0, 255, 0),
            'DARK_GREEN': (0, 128, 0),
            'BRIGHT_BLUE': (0, 0, 255),
            'BRIGHT_YELLOW': (255, 255, 0),
            'BRIGHT_CYAN': (0, 255, 255),
            'BRIGHT_MAGENTA': (255, 0, 255),
            'ORANGE': (255, 128, 0),
            'PURPLE': (128, 0, 255),
            'LIME': (128, 255, 0),
            'PINK': (255, 128, 255),
            'TEAL': (0, 128, 128),
            'AMBER': (255, 191, 0),
            'BLOOD_RED': (139, 0, 0)
        }
        
        # Animation variables
        self.frame_count = 0
        self.text_pulse = 0
        self.border_colors = [
            self.RETRO_COLORS['BRIGHT_RED'],
            self.RETRO_COLORS['BRIGHT_YELLOW'], 
            self.RETRO_COLORS['BRIGHT_GREEN'],
            self.RETRO_COLORS['BRIGHT_CYAN'],
            self.RETRO_COLORS['BRIGHT_BLUE'],
            self.RETRO_COLORS['BRIGHT_MAGENTA']
        ]
        
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
        
        # Configuration - Updated URL
        self.form_url = "http://shmeglsdoombox.spoon.rip"
        self.mqtt_enabled = MQTT_AVAILABLE
        
        # Initialize components
        self.init_database()
        self.qr_image = self.generate_large_qr_code()
        self.setup_retro_fonts()
        
        # Effects
        self.retro_effects = RetroEffects()
        self.retro_font = RetroFont()
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        
        # Setup MQTT if available
        if self.mqtt_enabled:
            self.setup_mqtt()
        
        print("Enhanced Retro DoomBox Kiosk initialized successfully!")

    def setup_retro_fonts(self):
        """Initialize retro-style fonts"""
        try:
            # Try to load a monospace font for better retro feel
            self.font_huge = pygame.font.Font(None, 120)     # Title
            self.font_large = pygame.font.Font(None, 72)     # Subtitle  
            self.font_medium = pygame.font.Font(None, 48)    # Headers
            self.font_small = pygame.font.Font(None, 32)     # Content
            self.font_tiny = pygame.font.Font(None, 24)      # Footer
            
            # Make fonts look more pixelated by disabling antialiasing
            self.pixel_fonts = True
        except:
            # Fallback fonts
            self.font_huge = pygame.font.SysFont('courier', 120, bold=True)
            self.font_large = pygame.font.SysFont('courier', 72, bold=True)
            self.font_medium = pygame.font.SysFont('courier', 48, bold=True)
            self.font_small = pygame.font.SysFont('courier', 32)
            self.font_tiny = pygame.font.SysFont('courier', 24)
            self.pixel_fonts = False

    def render_pixel_text(self, text, font, color, glow=False):
        """Render text with retro pixelated style"""
        # Render without antialiasing for crisp pixels
        surface = font.render(text, False, color)
        
        if glow:
            # Add glow effect
            glow_color = tuple(min(255, c + 50) for c in color[:3])
            self.retro_effects.add_glow(surface, glow_color)
        
        return surface

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

    def generate_large_qr_code(self):
        """Generate large QR code for the registration form"""
        try:
            qr = qrcode.QRCode(
                version=3,  # Larger version for bigger QR code
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=12,  # Much larger boxes
                border=8,     # Bigger border
            )
            qr.add_data(self.form_url)
            qr.make(fit=True)
            
            # Create QR image with retro colors
            qr_img = qr.make_image(
                fill_color=self.RETRO_COLORS['WHITE'], 
                back_color=self.RETRO_COLORS['BLACK']
            )
            
            # Make it much larger - 400x400 pixels
            qr_img = qr_img.resize((400, 400), resample=0)  # No interpolation for crisp pixels
            
            # Convert to pygame surface
            mode = qr_img.mode
            size = qr_img.size
            data = qr_img.tobytes()
            qr_surface = pygame.image.fromstring(data, size, mode)
            
            # Add retro border frame
            bordered_surface = pygame.Surface((size[0] + 16, size[1] + 16))
            bordered_surface.fill(self.RETRO_COLORS['DARK_GRAY'])
            
            # Add animated border
            border_surface = pygame.Surface((size[0] + 16, size[1] + 16))
            self.retro_effects.create_border_frame(border_surface, 4, self.border_colors)
            
            bordered_surface.blit(qr_surface, (8, 8))
            bordered_surface.blit(border_surface, (0, 0))
            
            print("Large retro QR code generated successfully")
            return bordered_surface
            
        except Exception as e:
            print(f"QR code generation error: {e}")
            # Create fallback QR placeholder
            surface = pygame.Surface((400, 400))
            surface.fill(self.RETRO_COLORS['DARK_GRAY'])
            
            # Draw retro-style "QR ERROR" text
            error_text = self.render_pixel_text("QR ERROR", self.font_medium, self.RETRO_COLORS['BRIGHT_RED'])
            text_rect = error_text.get_rect(center=(200, 200))
            surface.blit(error_text, text_rect)
            
            # Add border
            pygame.draw.rect(surface, self.RETRO_COLORS['BRIGHT_RED'], (0, 0, 400, 400), 4)
            
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

    def draw_animated_title(self):
        """Draw animated title with retro effects"""
        # Pulsing title
        pulse = math.sin(self.frame_count * 0.1) * 0.3 + 1.0
        title_color = tuple(int(c * pulse) for c in self.RETRO_COLORS['BLOOD_RED'])
        title_color = tuple(min(255, max(0, c)) for c in title_color)
        
        title = self.render_pixel_text("shmegl's DoomBox", self.font_huge, title_color, glow=True)
        title_rect = title.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=40)
        self.screen.blit(title, title_rect)
        
        # Animated subtitle
        subtitle_colors = [self.RETRO_COLORS['BRIGHT_YELLOW'], self.RETRO_COLORS['BRIGHT_CYAN']]
        color_index = (self.frame_count // 30) % len(subtitle_colors)
        subtitle_color = subtitle_colors[color_index]
        
        subtitle = self.render_pixel_text("Highest score gets a free tattoo!", self.font_large, subtitle_color)
        subtitle_rect = subtitle.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=140)
        self.screen.blit(subtitle, subtitle_rect)

    def draw_retro_ui_frame(self, x, y, width, height, title=""):
        """Draw retro-style UI frame"""
        # Main frame
        frame_surface = pygame.Surface((width, height))
        frame_surface.fill(self.RETRO_COLORS['DARK_GRAY'])
        
        # Border with animated colors
        border_color_index = (self.frame_count // 20) % len(self.border_colors)
        border_color = self.border_colors[border_color_index]
        
        pygame.draw.rect(frame_surface, border_color, (0, 0, width, height), 3)
        pygame.draw.rect(frame_surface, self.RETRO_COLORS['BLACK'], (3, 3, width-6, height-6), 1)
        
        # Title bar if provided
        if title:
            title_surface = self.render_pixel_text(title, self.font_medium, self.RETRO_COLORS['BRIGHT_WHITE'])
            title_rect = title_surface.get_rect(centerx=width//2, y=10)
            frame_surface.blit(title_surface, title_rect)
        
        self.screen.blit(frame_surface, (x, y))
        return frame_surface

    def draw_screen(self):
        """Draw the enhanced retro kiosk screen"""
        # Clear screen with dark background
        self.screen.fill(self.RETRO_COLORS['BLACK'])
        
        # Draw animated grid background
        grid_color = (*self.RETRO_COLORS['DARK_GRAY'][:3], 50)
        for x in range(0, self.DISPLAY_SIZE[0], 40):
            pygame.draw.line(self.screen, self.RETRO_COLORS['DARK_GRAY'], (x, 0), (x, self.DISPLAY_SIZE[1]))
        for y in range(0, self.DISPLAY_SIZE[1], 40):
            pygame.draw.line(self.screen, self.RETRO_COLORS['DARK_GRAY'], (0, y), (self.DISPLAY_SIZE[0], y))
        
        # Animated title
        self.draw_animated_title()
        
        # Instruction text
        instruction = self.render_pixel_text("SCAN THE QR CODE TO ENTER THE BATTLE", 
                                           self.font_small, self.RETRO_COLORS['BRIGHT_GREEN'])
        instruction_rect = instruction.get_rect(centerx=self.DISPLAY_SIZE[0] // 2, y=220)
        self.screen.blit(instruction, instruction_rect)
        
        # Large QR Code in center-left
        qr_x = 100
        qr_y = 280
        
        # QR Frame
        qr_frame = self.draw_retro_ui_frame(qr_x - 20, qr_y - 20, 440, 480, "SCAN TO PLAY")
        
        # QR Code
        self.screen.blit(self.qr_image, (qr_x, qr_y))
        
        # QR Label with pulsing effect
        pulse = math.sin(self.frame_count * 0.2) * 0.5 + 1.0
        label_color = tuple(int(c * pulse) for c in self.RETRO_COLORS['BRIGHT_CYAN'])
        label_color = tuple(min(255, max(50, c)) for c in label_color)
        
        qr_label = self.render_pixel_text(">> SCAN TO ENTER <<", self.font_medium, label_color)
        qr_label_rect = qr_label.get_rect(centerx=qr_x + 200, y=qr_y + 420)
        self.screen.blit(qr_label, qr_label_rect)
        
        # High Scores section
        scores_x = 600
        scores_y = 280
        scores_width = 600
        scores_height = 480
        
        scores_frame = self.draw_retro_ui_frame(scores_x, scores_y, scores_width, scores_height, "TOP WARRIORS")
        
        scores = self.get_top_scores()
        y_offset = scores_y + 60
        
        if scores:
            for i, (name, score, timestamp, level) in enumerate(scores):
                # Different colors for top 3
                if i == 0:
                    color = self.RETRO_COLORS['BRIGHT_YELLOW']  # Gold
                    prefix = "👑"
                elif i == 1:
                    color = self.RETRO_COLORS['LIGHT_GRAY']     # Silver
                    prefix = "🥈"
                elif i == 2:
                    color = self.RETRO_COLORS['ORANGE']         # Bronze
                    prefix = "🥉"
                else:
                    color = self.RETRO_COLORS['WHITE']
                    prefix = f"{i+1:2d}."
                
                # Format player name
                display_name = name[:12] + "..." if len(name) > 12 else name
                score_text = f"{prefix} {display_name}: {score:,}"
                
                score_surface = self.render_pixel_text(score_text, self.font_small, color)
                self.screen.blit(score_surface, (scores_x + 20, y_offset + i * 35))
        else:
            no_scores = self.render_pixel_text("NO SCORES YET - BE THE FIRST!", 
                                             self.font_small, self.RETRO_COLORS['GRAY'])
            no_scores_rect = no_scores.get_rect(centerx=scores_x + scores_width//2, y=y_offset + 100)
            se
