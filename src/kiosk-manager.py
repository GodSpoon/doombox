#!/usr/bin/env python3
"""
shmegl's DoomBox Kiosk Application - Improved Layout
Optimized for 4:3 displays (1280x960) with clean, appealing design
Uses only Puffin fonts for consistent visual style
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
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
import importlib.util
from fallback_video_player import create_video_player

# Enhanced imports for MQTT and game integration will be loaded after logger setup

# Set up logging
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

# Enhanced imports for MQTT and game integration
try:
    # Add current directory to path for local imports
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Import with proper module names (handling hyphens)
    import importlib.util
    import paho.mqtt.client as mqtt
    
    # Import mqtt-client
    mqtt_spec = importlib.util.spec_from_file_location("mqtt_client", 
                                                      os.path.join(os.path.dirname(__file__), "mqtt-client.py"))
    mqtt_module = importlib.util.module_from_spec(mqtt_spec)
    mqtt_spec.loader.exec_module(mqtt_module)
    DoomBoxMQTTClient = mqtt_module.DoomBoxMQTTClient
    
    # Import game-launcher
    game_spec = importlib.util.spec_from_file_location("game_launcher", 
                                                      os.path.join(os.path.dirname(__file__), "game-launcher.py"))
    game_module = importlib.util.module_from_spec(game_spec)
    game_spec.loader.exec_module(game_module)
    GameLauncher = game_module.GameLauncher
    
    logger.info("Successfully imported DoomBox components")
    MQTT_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import DoomBox components: {e}")
    # Set dummy classes to prevent crashes
    class DoomBoxMQTTClient:
        def __init__(self, *args, **kwargs): pass
        def connect(self): return False
        def disconnect(self): pass
        def set_game_launcher(self, launcher): pass
    
    class GameLauncher:
        def __init__(self, *args, **kwargs): pass
        def launch_game(self, *args, **kwargs): return False
        def stop_game(self): pass
    
    MQTT_INTEGRATION_AVAILABLE = False

class CleanUIRenderer:
    """Handles clean, appealing visual design optimized for 4:3 displays"""

    def __init__(self, screen, display_size):
        self.screen = screen
        self.display_size = display_size
        self.frame_count = 0

        # Dark purple/light purple/off white color scheme
        self.COLORS = {
            # Primary colors
            'OFF_BLACK': (25, 20, 35),           # Deep dark background
            'DARK_PURPLE': (45, 35, 65),         # Primary dark purple
            'MEDIUM_PURPLE': (75, 60, 110),      # Medium purple
            'LIGHT_PURPLE': (140, 120, 180),     # Light purple accent
            
            # Text colors
            'OFF_WHITE': (250, 248, 255),        # Primary text
            'LIGHT_GRAY': (200, 195, 210),       # Secondary text
            'MEDIUM_GRAY': (160, 150, 170),      # Tertiary text
            
            # Accent colors
            'PURPLE_BLUE': (120, 100, 200),      # Links/interactive
            'SUCCESS_PURPLE': (160, 120, 200),   # Success states
            'WARNING_PURPLE': (200, 150, 180),   # Warnings
            'GOLD_PURPLE': (220, 180, 200),      # Highlights
            
            # Subtle effects
            'OVERLAY_DARK': (15, 10, 25),        # Overlays
            'BORDER_LIGHT': (100, 85, 130),      # Borders
        }

        # Layout constants for 4:3 (1280x960) optimization
        self.LAYOUT = {
            'HEADER_HEIGHT': 140,                 # Reduced to better match actual header content
            'MARGIN': 40,                         # Consistent margins
            'PADDING': 20,                        # Internal padding
            'BORDER_RADIUS': 12,                  # Modern rounded corners
            'QR_SIZE': 300,                       # Large enough but not overwhelming
            'CONTENT_WIDTH': 1200,                # Main content area width
            'SCORES_WIDTH': 500,                  # Leaderboard width
        }

        # Animation states (minimal for clean look)
        self.blink_timer = 0
        self.pulse_timer = 0

    def draw_rounded_rect(self, rect, radius=12, color=None, border_color=None, border_width=0):
        """Draw a rounded rectangle with optional border"""
        if color:
            # Create surface for rounded rect
            surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, rect[2], rect[3]), border_radius=radius)
            self.screen.blit(surf, (rect[0], rect[1]))
        
        if border_color and border_width > 0:
            surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
            pygame.draw.rect(surf, border_color, (0, 0, rect[2], rect[3]), 
                           width=border_width, border_radius=radius)
            self.screen.blit(surf, (rect[0], rect[1]))

    def draw_text_with_shadow(self, text, font, color, pos, shadow_color=None, shadow_offset=(2, 2)):
        """Draw text with subtle shadow for better readability"""
        if shadow_color:
            shadow_surf = font.render(text, True, shadow_color)
            self.screen.blit(shadow_surf, (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]))
        
        text_surf = font.render(text, True, color)
        self.screen.blit(text_surf, pos)
        return text_surf.get_rect(topleft=pos)

    def draw_gradient_background(self, rect, color1, color2, vertical=True):
        """Draw a subtle gradient background"""
        surf = pygame.Surface((rect[2], rect[3]))
        if vertical:
            for y in range(rect[3]):
                blend = y / rect[3]
                color = [
                    int(color1[i] * (1 - blend) + color2[i] * blend)
                    for i in range(3)
                ]
                pygame.draw.line(surf, color, (0, y), (rect[2], y))
        else:
            for x in range(rect[2]):
                blend = x / rect[2]
                color = [
                    int(color1[i] * (1 - blend) + color2[i] * blend)
                    for i in range(3)
                ]
                pygame.draw.line(surf, color, (x, 0), (x, rect[3]))
        
        self.screen.blit(surf, (rect[0], rect[1]))

    def update_animations(self):
        """Update minimal animation timers"""
        self.frame_count += 1
        self.blink_timer = (self.blink_timer + 0.02) % (2 * math.pi)
        self.pulse_timer = (self.pulse_timer + 0.01) % (2 * math.pi)



class DoomBoxKiosk:
    def __init__(self):
        logger.info("Initializing DoomBox Kiosk with improved layout...")
        
        # Display setup
        self.DISPLAY_SIZE = (1280, 960)  # 4:3 aspect ratio
        os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
        
        pygame.init()
        pygame.mixer.quit()  # Disable audio for performance
        
        self.screen = pygame.display.set_mode(self.DISPLAY_SIZE, pygame.FULLSCREEN)
        pygame.display.set_caption("shmegl's DoomBox")
        pygame.mouse.set_visible(False)
        
        # Initialize renderer
        self.ui = CleanUIRenderer(self.screen, self.DISPLAY_SIZE)
        
        # Application state
        self.running = True
        self.clock = pygame.time.Clock()
        self.form_url = "http://shmeglsdoombox.spoon.rip"
        self.video_paused = False  # Track video playback state
        self.kiosk_hidden = False  # Track if kiosk is hidden for game
        
        # Setup directories first
        self.setup_directories()
        
        # Setup fonts after directories are created
        self.setup_fonts()
        
        # Setup icons
        self.setup_icons()
        
        # Initialize components
        self.setup_qr_code()
        self.setup_database()
        self.setup_hardware_video_player()
        
        # Initialize game launcher and MQTT client
        self.setup_game_integration()
        
        logger.info("DoomBox Kiosk initialized successfully!")

    def setup_directories(self):
        """Setup required directories"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level from src/
        self.fonts_dir = os.path.join(self.base_dir, 'fonts')
        self.assets_dir = os.path.join(self.base_dir, 'assets')
        self.videos_dir = os.path.join(self.base_dir, 'vid')
        
        for directory in [self.fonts_dir, self.assets_dir, self.videos_dir]:
            os.makedirs(directory, exist_ok=True)

    def setup_fonts(self):
        """Setup Doom 2016 fonts for header and Puffin fonts for body text"""
        try:
            # Doom 2016 font paths
            doom_left_path = os.path.join(self.fonts_dir, "Doom2016Left-RpJDA.ttf")
            doom_right_path = os.path.join(self.fonts_dir, "Doom2016Right-VGz0z.ttf")
            doom_text_path = os.path.join(self.fonts_dir, "Doom2016Text-GOlBq.ttf")
            
            # Puffin font paths
            puffin_regular_path = os.path.join(self.fonts_dir, "Puffin Arcade Regular.ttf")
            puffin_liquid_path = os.path.join(self.fonts_dir, "Puffin Arcade Liquid.ttf")
            
            # Load Doom 2016 fonts for header
            if (os.path.exists(doom_left_path) and os.path.exists(doom_right_path) and os.path.exists(doom_text_path)):
                self.font_doom_left = pygame.font.Font(doom_left_path, 90)
                self.font_doom_right = pygame.font.Font(doom_right_path, 90)
                self.font_doom_text = pygame.font.Font(doom_text_path, 90)
                logger.info("Using Doom 2016 fonts for header")
            else:
                # Fallback to Puffin Liquid for header
                if os.path.exists(puffin_liquid_path):
                    self.font_doom_left = pygame.font.Font(puffin_liquid_path, 90)
                    self.font_doom_right = pygame.font.Font(puffin_liquid_path, 90)
                    self.font_doom_text = pygame.font.Font(puffin_liquid_path, 90)
                    logger.warning("Doom 2016 fonts not found, using Puffin Liquid for header")
                else:
                    self.font_doom_left = pygame.font.SysFont('arial', 90, bold=True)
                    self.font_doom_right = pygame.font.SysFont('arial', 90, bold=True)
                    self.font_doom_text = pygame.font.SysFont('arial', 90, bold=True)
                    logger.warning("Doom 2016 and Puffin fonts not found, using system font for header")
            
            # Check if Puffin Liquid exists and use it for titles
            if os.path.exists(puffin_liquid_path) and os.path.getsize(puffin_liquid_path) > 1000:
                self.font_title = pygame.font.Font(puffin_liquid_path, 72)
                self.font_subtitle = pygame.font.Font(puffin_liquid_path, 48)
                self.font_large = pygame.font.Font(puffin_liquid_path, 36)
                logger.info("Using Puffin Liquid for titles")
            else:
                # Fallback to system font for titles
                self.font_title = pygame.font.SysFont('arial', 72, bold=True)
                self.font_subtitle = pygame.font.SysFont('arial', 48, bold=True)
                self.font_large = pygame.font.SysFont('arial', 36, bold=True)
                logger.warning("Puffin Liquid not found, using system font for titles")
            
            # Use Puffin Regular for body text
            if os.path.exists(puffin_regular_path) and os.path.getsize(puffin_regular_path) > 1000:
                self.font_medium = pygame.font.Font(puffin_regular_path, 28)
                self.font_small = pygame.font.Font(puffin_regular_path, 22)
                self.font_tiny = pygame.font.Font(puffin_regular_path, 18)
                logger.info("Using Puffin Regular for body text")
            else:
                # Fallback fonts for body text
                self.font_medium = pygame.font.SysFont('arial', 28)
                self.font_small = pygame.font.SysFont('arial', 22)
                self.font_tiny = pygame.font.SysFont('arial', 18)
                logger.warning("Puffin Regular not found, using system font for body text")
            
            logger.info("Font setup complete")
        except Exception as e:
            logger.error(f"Font setup error: {e}")
            # Ultimate fallback
            self.font_doom_left = pygame.font.Font(None, 90)
            self.font_doom_right = pygame.font.Font(None, 90)
            self.font_doom_text = pygame.font.Font(None, 90)
            self.font_title = pygame.font.Font(None, 72)
            self.font_subtitle = pygame.font.Font(None, 48)
            self.font_large = pygame.font.Font(None, 36)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 22)
            self.font_tiny = pygame.font.Font(None, 18)

    def setup_qr_code(self):
        """Generate QR code for the form"""
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
            qr_img = qr_img.resize((self.ui.LAYOUT['QR_SIZE'], self.ui.LAYOUT['QR_SIZE']))
            
            # Convert PIL image to pygame surface using numpy
            qr_array = np.array(qr_img)
            
            # Handle different image modes
            if qr_img.mode == 'RGB':
                self.qr_surface = pygame.surfarray.make_surface(qr_array.swapaxes(0, 1))
            elif qr_img.mode == 'RGBA':
                self.qr_surface = pygame.surfarray.make_surface(qr_array[:, :, :3].swapaxes(0, 1))
            elif qr_img.mode == 'L':  # Grayscale
                # Convert grayscale to RGB
                qr_rgb = np.stack([qr_array, qr_array, qr_array], axis=2)
                self.qr_surface = pygame.surfarray.make_surface(qr_rgb.swapaxes(0, 1))
            else:
                # Convert to RGB and try again
                qr_img = qr_img.convert('RGB')
                qr_array = np.array(qr_img)
                self.qr_surface = pygame.surfarray.make_surface(qr_array.swapaxes(0, 1))
            
            logger.info("QR code generated successfully")
        except Exception as e:
            logger.error(f"QR code generation error: {e}")
            # Create placeholder QR code
            self.qr_surface = pygame.Surface((self.ui.LAYOUT['QR_SIZE'], self.ui.LAYOUT['QR_SIZE']))
            self.qr_surface.fill(self.ui.COLORS['LIGHT_GRAY'])
            
            # Draw placeholder text
            placeholder_text = self.font_medium.render("QR CODE", True, self.ui.COLORS['DARK_PURPLE'])
            text_rect = placeholder_text.get_rect(center=(self.ui.LAYOUT['QR_SIZE']//2, self.ui.LAYOUT['QR_SIZE']//2))
            self.qr_surface.blit(placeholder_text, text_rect)

    def setup_database(self):
        """Initialize scores database"""
        try:
            self.db_path = os.path.join(self.base_dir, 'doombox_scores.db')
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database setup error: {e}")

    def setup_hardware_video_player(self):
        """Setup optimized video player with hardware acceleration fallback"""
        try:
            # Try to use hardware acceleration first, fall back to cached/simple players
            self.video_player = create_video_player(
                video_dir=self.videos_dir,
                display_size=self.DISPLAY_SIZE,
                prefer_hardware=True
            )
            
            if self.video_player:
                logger.info("Video player started successfully")
                stats = self.video_player.get_stats()
                logger.info(f"Video player stats: {stats}")
                
                # Log performance info
                if 'hardware_acceleration' in stats:
                    if stats['hardware_acceleration']:
                        logger.info("✅ Using hardware-accelerated video decoding")
                    else:
                        logger.warning("⚠️ Using software video decoding - performance may be limited")
                
                if 'cache_frames' in stats:
                    logger.info(f"📹 Cached {stats['cache_frames']} frames ({stats.get('cache_size_mb', 0):.1f} MB)")
                    
            else:
                logger.warning("Failed to start any video player")
                
        except Exception as e:
            logger.error(f"Error setting up video player: {e}")
            self.video_player = None

    def get_top_scores(self, limit=10):
        """Get top scores from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT player_name, score FROM scores 
                ORDER BY score DESC, timestamp ASC 
                LIMIT ?
            ''', (limit,))
            
            scores = cursor.fetchall()
            conn.close()
            return scores
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return [("PLAYER", 0) for _ in range(3)]  # Dummy data

    def setup_icons(self):
        """Load game icons and graphics"""
        try:
            self.icons_dir = os.path.join(self.base_dir, 'icons')
            
            # Load skull icon
            skull_path = os.path.join(self.icons_dir, 'pixelart_skull.png')
            if os.path.exists(skull_path):
                self.skull_icon = pygame.image.load(skull_path).convert_alpha()
                self.skull_icon = pygame.transform.scale(self.skull_icon, (64, 64))
                logger.info("Loaded skull icon")
            else:
                self.skull_icon = None
                logger.warning("Skull icon not found")
            
            # Load trophy icon
            trophy_path = os.path.join(self.icons_dir, 'solid', 'trophy.png')
            if os.path.exists(trophy_path):
                self.trophy_icon = pygame.image.load(trophy_path).convert_alpha()
                self.trophy_icon = pygame.transform.scale(self.trophy_icon, (32, 32))
                logger.info("Loaded trophy icon")
            else:
                self.trophy_icon = None
                logger.warning("Trophy icon not found")
            
            # Load crown icon
            crown_path = os.path.join(self.icons_dir, 'solid', 'crown.png')
            if os.path.exists(crown_path):
                self.crown_icon = pygame.image.load(crown_path).convert_alpha()
                self.crown_icon = pygame.transform.scale(self.crown_icon, (32, 32))
                logger.info("Loaded crown icon")
            else:
                self.crown_icon = None
                logger.warning("Crown icon not found")
            
            logger.info("Icon setup complete")
        except Exception as e:
            logger.error(f"Icon setup error: {e}")
            self.skull_icon = None
            self.trophy_icon = None
            self.crown_icon = None

    def setup_game_integration(self):
        """Initialize game launcher and MQTT integration"""
        try:
            logger.info("Setting up game integration...")
            
            if not MQTT_INTEGRATION_AVAILABLE:
                logger.warning("MQTT integration not available, skipping...")
                self.game_launcher = None
                self.mqtt_client = None
                return
            
            # Initialize game launcher
            self.game_launcher = GameLauncher()
            
            # Add game state callback to handle video playback
            self.game_launcher.add_game_state_callback(self._on_game_state_change)
            
            logger.info("Game launcher initialized")
            
            # Initialize MQTT client
            self.mqtt_client = DoomBoxMQTTClient()
            
            # Connect game launcher to MQTT client
            self.mqtt_client.set_game_launcher(self.game_launcher)
            
            # Connect to MQTT broker in a separate thread
            def connect_mqtt():
                try:
                    if self.mqtt_client.connect():
                        logger.info("✅ MQTT client connected successfully")
                        # Publish initial status
                        try:
                            self.mqtt_client._publish_system_status()
                        except:
                            # Fallback if direct method doesn't work
                            pass
                    else:
                        logger.warning("❌ Failed to connect to MQTT broker")
                except Exception as e:
                    logger.error(f"MQTT connection error: {e}")
            
            # Start MQTT connection in background
            import threading
            mqtt_thread = threading.Thread(target=connect_mqtt, daemon=True)
            mqtt_thread.start()
            
            logger.info("Game integration setup complete")
            
        except Exception as e:
            logger.error(f"Game integration setup error: {e}")
            # Set dummy objects to prevent crashes
            self.game_launcher = None
            self.mqtt_client = None
    
    def _on_game_state_change(self, old_state, new_state, player_name):
        """Handle game state changes - properly close kiosk when game starts"""
        logger.info(f"Game state changed: {old_state} -> {new_state} (player: {player_name})")
        
        if new_state in ["starting", "running"]:
            # Game is starting or running - properly hide kiosk and stop all resources
            logger.info("Game starting - hiding kiosk and stopping all resources for game")
            
            # Stop video player entirely to free up resources
            if self.video_player:
                self.video_player.stop()
                self.video_player = None  # Completely remove reference
                logger.info("Video player stopped and destroyed")
            
            # Hide pygame window properly without quitting display subsystem
            try:
                # Minimize/iconify the window to give dsda-doom full access to display
                pygame.display.iconify()
                # Create a minimal black surface to reduce GPU usage
                black_surface = pygame.Surface((1, 1))
                black_surface.fill((0, 0, 0))
                self.screen.blit(black_surface, (0, 0))
                pygame.display.flip()
                logger.info("Kiosk window minimized and display freed for game")
            except Exception as e:
                logger.warning(f"Could not minimize kiosk window: {e}")
            
            # Set video as stopped and mark kiosk as hidden
            self.video_paused = True
            self.kiosk_hidden = True
            
        elif new_state in ["idle", "finished"]:
            # Game is finished or idle - restore kiosk and restart video
            logger.info("Game finished - fully restoring kiosk and restarting all components")
            
            # Wait a moment for game to fully exit and release resources
            time.sleep(2)
            
            # Restore kiosk display - just make sure window is restored
            try:
                # Restore the window from minimized state
                # Don't need to reinitialize pygame display as it's still active
                pygame.mouse.set_visible(False)
                logger.info("Kiosk window restored to foreground")
            except Exception as e:
                logger.error(f"Could not restore kiosk window: {e}")
            
            # Restart video player
            self.setup_hardware_video_player()
            
            # Resume video playback and show kiosk
            self.video_paused = False
            self.kiosk_hidden = False
            logger.info("Video playback and kiosk fully resumed")

    def draw_doom_header(self, title_text, x, y):
        """Draw header with Doom 2016 fonts and skull icons"""
        # Split title into first, middle, and last characters
        if len(title_text) >= 3:
            first_char = title_text[0]
            middle_text = title_text[1:-1]
            last_char = title_text[-1]
        else:
            first_char = title_text[0] if len(title_text) > 0 else ""
            middle_text = title_text[1:] if len(title_text) > 1 else ""
            last_char = ""
        
        # Render each part
        parts = []
        if first_char:
            first_surf = self.font_doom_left.render(first_char, True, (220, 50, 50))  # Doom red color
            parts.append(first_surf)
        
        if middle_text:
            middle_surf = self.font_doom_text.render(middle_text, True, (220, 50, 50))  # Doom red color
            parts.append(middle_surf)
        
        if last_char:
            last_surf = self.font_doom_right.render(last_char, True, (220, 50, 50))  # Doom red color
            parts.append(last_surf)
        
        # Calculate total width
        total_width = sum(part.get_width() for part in parts)
        
        # Add skull icon spacing
        skull_spacing = 80 if self.skull_icon else 0
        total_width_with_skulls = total_width + (skull_spacing * 2)
        
        # Center the entire header
        start_x = x - total_width_with_skulls // 2
        
        # Draw left skull
        if self.skull_icon:
            skull_y = y + 10  # Slightly lower to align with text
            self.screen.blit(self.skull_icon, (start_x, skull_y))
        
        # Draw text parts with proper black drop shadow
        current_x = start_x + skull_spacing
        for i, part in enumerate(parts):
            # Get the original text for shadow rendering
            if i == 0 and first_char:
                shadow_text = self.font_doom_left.render(first_char, True, (0, 0, 0))  # Black shadow
            elif i == len(parts) - 1 and last_char:
                shadow_text = self.font_doom_right.render(last_char, True, (0, 0, 0))  # Black shadow
            else:
                shadow_text = self.font_doom_text.render(middle_text, True, (0, 0, 0))  # Black shadow
            
            # Draw black drop shadow (larger offset for more dramatic effect)
            self.screen.blit(shadow_text, (current_x + 4, y + 4))
            
            # Draw main text
            self.screen.blit(part, (current_x, y))
            current_x += part.get_width()
        
        # Draw right skull (mirrored)
        if self.skull_icon:
            skull_y = y + 10  # Slightly lower to align with text
            mirrored_skull = pygame.transform.flip(self.skull_icon, True, False)  # Flip horizontally
            self.screen.blit(mirrored_skull, (start_x + total_width_with_skulls - 64, skull_y))
        
        return total_width_with_skulls

    def draw_main_screen(self):
        """Draw the main kiosk screen with purple color scheme and visible video background"""
        
        # Background - Hardware-accelerated video (only if not paused)
        if self.video_player and not self.video_paused:
            video_frame = self.video_player.get_frame()
            if video_frame:
                # Apply subtle purple tint to video instead of heavy darkening
                self.screen.blit(video_frame, (0, 0))
                
                # Light purple overlay for better contrast but still visible video
                video_overlay = pygame.Surface(self.DISPLAY_SIZE)
                video_overlay.fill(self.ui.COLORS['DARK_PURPLE'])
                video_overlay.set_alpha(60)  # Much lighter overlay
                self.screen.blit(video_overlay, (0, 0))
            else:
                # Gradient background with purple theme
                self.ui.draw_gradient_background(
                    (0, 0, self.DISPLAY_SIZE[0], self.DISPLAY_SIZE[1]),
                    self.ui.COLORS['OFF_BLACK'],
                    self.ui.COLORS['DARK_PURPLE']
                )
        else:
            # Show static background when video is paused or unavailable
            self.ui.draw_gradient_background(
                (0, 0, self.DISPLAY_SIZE[0], self.DISPLAY_SIZE[1]),
                self.ui.COLORS['OFF_BLACK'],
                self.ui.COLORS['DARK_PURPLE']
            )
            
            # If video is paused due to game, show a message
            if self.video_paused:
                game_status_text = "GAME IN PROGRESS"
                game_status_surface = self.font_large.render(game_status_text, True, self.ui.COLORS['GOLD_PURPLE'])
                status_rect = game_status_surface.get_rect(center=(self.DISPLAY_SIZE[0]//2, self.DISPLAY_SIZE[1]//2))
                
                # Add background for better visibility
                bg_rect = pygame.Rect(status_rect.x - 20, status_rect.y - 10, status_rect.width + 40, status_rect.height + 20)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(bg_surface, (*self.ui.COLORS['OFF_BLACK'], 180), (0, 0, bg_rect.width, bg_rect.height), border_radius=12)
                self.screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
                
                self.screen.blit(game_status_surface, status_rect)
                
                # Show current player if available
                if hasattr(self, 'game_launcher') and self.game_launcher and self.game_launcher.current_player:
                    player_text = f"Player: {self.game_launcher.current_player}"
                    player_surface = self.font_medium.render(player_text, True, self.ui.COLORS['LIGHT_PURPLE'])
                    player_rect = player_surface.get_rect(center=(self.DISPLAY_SIZE[0]//2, self.DISPLAY_SIZE[1]//2 + 60))
                    self.screen.blit(player_surface, player_rect)
                
                return  # Don't draw the normal kiosk interface when game is running

        # === HEADER SECTION ===
        # Remove header background div - let header text appear directly on video
        
        # Main title with Doom 2016 font and skull icons (no background)
        title_y = 20
        self.draw_doom_header(
            "Slaughter with Shmegl",
            self.DISPLAY_SIZE[0]//2,
            title_y
        )

        # Subtitle
        subtitle_y = title_y + 95
        self.ui.draw_text_with_shadow(
            "Get the high score on Doom to win a free tattoo from Petra",
            self.font_subtitle,
            self.ui.COLORS['WARNING_PURPLE'],
            (self.DISPLAY_SIZE[0]//2 - self.font_subtitle.size("Get the high score on Doom to win a free tattoo from Petra")[0]//2, subtitle_y),
            self.ui.COLORS['OFF_BLACK'],
            (2, 2)
        )

        # === MAIN CONTENT AREA ===
        content_y = self.ui.LAYOUT['HEADER_HEIGHT'] + self.ui.LAYOUT['MARGIN']
        content_height = self.DISPLAY_SIZE[1] - content_y - self.ui.LAYOUT['MARGIN']

        # Left side - QR Code section
        qr_section_width = 400
        qr_section_x = self.ui.LAYOUT['MARGIN']
        qr_section_rect = (qr_section_x, content_y, qr_section_width, content_height)
        
        # QR code rounded background box with 50% opacity
        qr_bg_surface = pygame.Surface((qr_section_rect[2], qr_section_rect[3]), pygame.SRCALPHA)
        qr_bg_color = (*self.ui.COLORS['OVERLAY_DARK'], 128)  # 50% opacity (128/255)
        pygame.draw.rect(qr_bg_surface, qr_bg_color, (0, 0, qr_section_rect[2], qr_section_rect[3]), border_radius=self.ui.LAYOUT['BORDER_RADIUS'])
        self.screen.blit(qr_bg_surface, (qr_section_rect[0], qr_section_rect[1]))
        
        # Optional border
        self.ui.draw_rounded_rect(
            qr_section_rect,
            self.ui.LAYOUT['BORDER_RADIUS'],
            None,
            self.ui.COLORS['BORDER_LIGHT'],
            2
        )

        # QR section title - split into two lines
        qr_title_y = content_y + self.ui.LAYOUT['PADDING']
        qr_title_lines = [
            "Scan the QR code to enter",
            "your name and play"
        ]
        for i, line in enumerate(qr_title_lines):
            line_y = qr_title_y + i * 30
            self.ui.draw_text_with_shadow(
                line,
                self.font_medium,
                self.ui.COLORS['PURPLE_BLUE'],
                (qr_section_x + qr_section_width//2 - self.font_medium.size(line)[0]//2, line_y),
                self.ui.COLORS['OFF_BLACK']
            )

        # QR Code - Properly centered in the section with extra space for two-line title
        qr_y = qr_title_y + 80
        qr_x = qr_section_x + (qr_section_width - self.ui.LAYOUT['QR_SIZE']) // 2
        
        # QR background with purple tint
        qr_bg_rect = (qr_x - 15, qr_y - 15, self.ui.LAYOUT['QR_SIZE'] + 30, self.ui.LAYOUT['QR_SIZE'] + 30)
        self.ui.draw_rounded_rect(qr_bg_rect, 12, self.ui.COLORS['OFF_WHITE'])
        
        # Add subtle purple border
        self.ui.draw_rounded_rect(qr_bg_rect, 12, None, self.ui.COLORS['LIGHT_PURPLE'], 3)
        
        # Center the QR code perfectly
        qr_centered_x = qr_section_x + (qr_section_width - self.ui.LAYOUT['QR_SIZE']) // 2
        qr_centered_y = qr_y
        self.screen.blit(self.qr_surface, (qr_centered_x, qr_centered_y))

        # URL below QR - centered
        url_y = qr_centered_y + self.ui.LAYOUT['QR_SIZE'] + 25
        url_lines = [
            "shmeglsdoombox",
            ".spoon.rip"
        ]
        for i, line in enumerate(url_lines):
            line_y = url_y + i * 25
            self.ui.draw_text_with_shadow(
                line,
                self.font_small,
                self.ui.COLORS['LIGHT_GRAY'],
                (qr_section_x + qr_section_width//2 - self.font_small.size(line)[0]//2, line_y),
                self.ui.COLORS['OFF_BLACK']
            )

        # Instagram requirement text
        instagram_y = url_y + 60
        instagram_lines = [
            "Contestants must follow petra on",
            "Instagram @shmegl & share their",
            "last post to be able to win"
        ]
        for i, line in enumerate(instagram_lines):
            line_y = instagram_y + i * 20
            self.ui.draw_text_with_shadow(
                line,
                self.font_tiny,
                self.ui.COLORS['MEDIUM_GRAY'],
                (qr_section_x + qr_section_width//2 - self.font_tiny.size(line)[0]//2, line_y),
                self.ui.COLORS['OFF_BLACK']
            )

        # Right side - Leaderboard section
        scores_section_x = qr_section_x + qr_section_width + self.ui.LAYOUT['MARGIN']
        scores_section_width = self.DISPLAY_SIZE[0] - scores_section_x - self.ui.LAYOUT['MARGIN']
        scores_section_rect = (scores_section_x, content_y, scores_section_width, content_height)
        
        # Scores rounded background box with 50% opacity
        scores_bg_surface = pygame.Surface((scores_section_rect[2], scores_section_rect[3]), pygame.SRCALPHA)
        scores_bg_color = (*self.ui.COLORS['OVERLAY_DARK'], 128)  # 50% opacity (128/255)
        pygame.draw.rect(scores_bg_surface, scores_bg_color, (0, 0, scores_section_rect[2], scores_section_rect[3]), border_radius=self.ui.LAYOUT['BORDER_RADIUS'])
        self.screen.blit(scores_bg_surface, (scores_section_rect[0], scores_section_rect[1]))
        
        # Optional border
        self.ui.draw_rounded_rect(
            scores_section_rect,
            self.ui.LAYOUT['BORDER_RADIUS'],
            None,
            self.ui.COLORS['BORDER_LIGHT'],
            2
        )

        # Leaderboard title with trophy icon
        scores_title_y = content_y + self.ui.LAYOUT['PADDING']
        title_text = "TOP SCORES"
        title_width = self.font_large.size(title_text)[0]
        
        # Center the title text
        title_x = scores_section_x + scores_section_width//2 - title_width//2
        
        # Draw trophy icons on either side of the text
        if self.trophy_icon:
            trophy_y = scores_title_y + 5  # Slightly lower to align with text
            trophy_spacing = 15  # Space between text and trophies
            
            # Tint the trophy icons gold
            trophy_tinted = self.trophy_icon.copy()
            trophy_tinted.fill(self.ui.COLORS['GOLD_PURPLE'], special_flags=pygame.BLEND_MULT)
            
            # Left trophy (before text)
            self.screen.blit(trophy_tinted, (title_x - trophy_spacing - 32, trophy_y))
            
            # Right trophy (after text)
            self.screen.blit(trophy_tinted, (title_x + title_width + trophy_spacing, trophy_y))
        
        # Draw title text (centered)
        self.ui.draw_text_with_shadow(
            title_text,
            self.font_large,
            self.ui.COLORS['GOLD_PURPLE'],
            (title_x, scores_title_y),
            self.ui.COLORS['OFF_BLACK']
        )

        # Score entries
        scores = self.get_top_scores(8)  # Show top 8 for clean layout
        scores_start_y = scores_title_y + 60
        line_height = 50

        for i, (player_name, score) in enumerate(scores):
            entry_y = scores_start_y + i * line_height
            
            # Rank colors with purple theme and proper icons
            if i == 0:
                rank_color = self.ui.COLORS['GOLD_PURPLE']
                name_color = self.ui.COLORS['GOLD_PURPLE']
                rank_icon = self.crown_icon
            elif i == 1:
                rank_color = self.ui.COLORS['LIGHT_PURPLE']
                name_color = self.ui.COLORS['LIGHT_PURPLE']
                rank_icon = None  # No specific icon for 2nd place
            elif i == 2:
                rank_color = self.ui.COLORS['WARNING_PURPLE']
                name_color = self.ui.COLORS['WARNING_PURPLE']
                rank_icon = None  # No specific icon for 3rd place
            else:
                rank_color = self.ui.COLORS['MEDIUM_GRAY']
                name_color = self.ui.COLORS['OFF_WHITE']
                rank_icon = None

            # Draw rank icon (only for first place)
            icon_offset = 0
            if rank_icon:
                icon_y = entry_y + 8  # Center with text
                # Tint the crown icon gold
                crown_tinted = rank_icon.copy()
                crown_tinted.fill(self.ui.COLORS['GOLD_PURPLE'], special_flags=pygame.BLEND_MULT)
                self.screen.blit(crown_tinted, (scores_section_x + 15, icon_y))
                icon_offset = 40

            # Rank number
            rank_text = f"{i+1}."
            self.ui.draw_text_with_shadow(
                rank_text,
                self.font_medium,
                rank_color,
                (scores_section_x + 15 + icon_offset, entry_y),
                self.ui.COLORS['OFF_BLACK']
            )

            # Player name (truncate if too long)
            display_name = player_name[:15] + "..." if len(player_name) > 15 else player_name
            self.ui.draw_text_with_shadow(
                display_name,
                self.font_medium,
                name_color,
                (scores_section_x + 65 + icon_offset, entry_y),
                self.ui.COLORS['OFF_BLACK']
            )

            # Score
            score_text = f"{score:,}"
            score_width = self.font_medium.size(score_text)[0]
            self.ui.draw_text_with_shadow(
                score_text,
                self.font_medium,
                self.ui.COLORS['PURPLE_BLUE'],
                (scores_section_x + scores_section_width - score_width - 30, entry_y),
                self.ui.COLORS['OFF_BLACK']
            )

        # Update animations
        self.ui.update_animations()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def run(self):
        """Main kiosk loop with improved performance"""
        logger.info("Starting DoomBox kiosk main loop")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            while self.running:
                # Skip main loop if kiosk is hidden for game
                if hasattr(self, 'kiosk_hidden') and self.kiosk_hidden:
                    # Kiosk is hidden while game is running - just sleep to avoid busy loop
                    time.sleep(1)
                    continue
                
                # Handle events only if kiosk is visible
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_F11:
                            pygame.display.toggle_fullscreen()
                        elif event.key == pygame.K_g:  # Test key to launch game
                            if hasattr(self, 'game_launcher') and self.game_launcher:
                                if not self.game_launcher.is_game_running():
                                    logger.info("Test game launch triggered")
                                    self.game_launcher.launch_game("TestPlayer")

                # Draw main screen only if kiosk is visible
                if hasattr(self, 'screen') and self.screen:
                    self.draw_main_screen()
                    
                    # Update display
                    pygame.display.flip()
                
                self.clock.tick(30)  # 30 FPS for smooth performance on ARM

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean shutdown"""
        logger.info("Cleaning up DoomBox kiosk...")
        
        # Clean up MQTT client
        if hasattr(self, 'mqtt_client') and self.mqtt_client:
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        # Clean up game launcher
        if hasattr(self, 'game_launcher') and self.game_launcher:
            self.game_launcher.stop_game()
            self.game_launcher.monitor_running = False
            logger.info("Game launcher stopped")
        
        if hasattr(self, 'video_player') and self.video_player:
            self.video_player.stop()
            logger.info("Hardware video player stopped")
        
        pygame.quit()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    try:
        kiosk = DoomBoxKiosk()
        kiosk.run()
    except Exception as e:
        logger.error(f"Failed to start kiosk: {e}")
        sys.exit(1)