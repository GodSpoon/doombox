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
            'HEADER_HEIGHT': 180,                 # Reduced from 25% to fixed height
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
        
        # Setup directories first
        self.setup_directories()
        
        # Setup fonts after directories are created
        self.setup_fonts()
        
        # Initialize components
        self.setup_qr_code()
        self.setup_database()
        self.load_background_video()
        
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
        """Setup Puffin fonts with Liquid for headlines and Regular for body text"""
        try:
            # Puffin font paths
            puffin_regular_path = os.path.join(self.fonts_dir, "Puffin Arcade Regular.ttf")
            puffin_liquid_path = os.path.join(self.fonts_dir, "Puffin Arcade Liquid.ttf")
            
            # Check if Puffin Liquid exists and use it for headlines
            if os.path.exists(puffin_liquid_path) and os.path.getsize(puffin_liquid_path) > 1000:
                self.font_title = pygame.font.Font(puffin_liquid_path, 72)
                self.font_subtitle = pygame.font.Font(puffin_liquid_path, 48)
                self.font_large = pygame.font.Font(puffin_liquid_path, 36)
                logger.info("Using Puffin Liquid for headlines")
            else:
                # Fallback to system font for headlines
                self.font_title = pygame.font.SysFont('arial', 72, bold=True)
                self.font_subtitle = pygame.font.SysFont('arial', 48, bold=True)
                self.font_large = pygame.font.SysFont('arial', 36, bold=True)
                logger.warning("Puffin Liquid not found, using system font for headlines")
            
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

    def load_background_video(self):
        """Load and setup background video cycling through all available videos in random order"""
        try:
            self.video_files = []
            if os.path.exists(self.videos_dir):
                # Get all video files and shuffle them for random order
                all_files = [f for f in os.listdir(self.videos_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
                self.video_files = sorted(all_files)  # Sort first for consistent behavior
                random.shuffle(self.video_files)  # Then shuffle for random order
            
            if self.video_files:
                self.current_video_index = 0
                self.video_cap = None
                self.video_frame_count = 0
                self.current_video_frame = 0
                self.video_switch_timer = 0
                self.video_switch_interval = 300  # Switch video every 10 seconds at 30fps
                
                # Load first video
                self.load_next_video()
                logger.info(f"Loaded {len(self.video_files)} background videos in random order")
            else:
                self.video_cap = None
                self.video_files = []
                logger.info("No background videos found")
        except Exception as e:
            logger.error(f"Video setup error: {e}")
            self.video_cap = None
            self.video_files = []

    def load_next_video(self):
        """Load the next video in the random sequence"""
        try:
            if not self.video_files:
                return
                
            if self.video_cap:
                self.video_cap.release()
            
            video_path = os.path.join(self.videos_dir, self.video_files[self.current_video_index])
            self.video_cap = cv2.VideoCapture(video_path)
            self.video_frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_video_frame = 0
            
            logger.info(f"Loaded video: {self.video_files[self.current_video_index]}")
            
            # Move to next video in the shuffled list
            self.current_video_index = (self.current_video_index + 1) % len(self.video_files)
            
            # If we've cycled through all videos, shuffle the list again for a new random order
            if self.current_video_index == 0:
                random.shuffle(self.video_files)
                logger.info("Reshuffled video playlist for new random order")
            
        except Exception as e:
            logger.error(f"Error loading video: {e}")
            self.video_cap = None

    def get_video_frame(self):
        """Get current video frame with cycling and better visibility"""
        if not self.video_cap or not self.video_files:
            return None
        
        try:
            # Check if we should switch to next video
            self.video_switch_timer += 1
            if self.video_switch_timer >= self.video_switch_interval:
                self.video_switch_timer = 0
                self.load_next_video()
                if not self.video_cap:
                    return None
            
            ret, frame = self.video_cap.read()
            if not ret:
                # If video ended, load next video
                self.load_next_video()
                if self.video_cap:
                    ret, frame = self.video_cap.read()
                else:
                    return None
            
            if ret:
                # Convert to pygame surface
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, self.DISPLAY_SIZE)
                return pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        except Exception as e:
            logger.error(f"Video frame error: {e}")
            # Try to load next video on error
            self.load_next_video()
        
        return None

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

    def draw_main_screen(self):
        """Draw the main kiosk screen with purple color scheme and visible video background"""
        
        # Background - Make video more visible
        video_frame = self.get_video_frame()
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

        # === HEADER SECTION ===
        header_rect = (0, 0, self.DISPLAY_SIZE[0], self.ui.LAYOUT['HEADER_HEIGHT'])
        
        # Header background with transparency
        header_overlay = pygame.Surface((header_rect[2], header_rect[3]))
        header_overlay.fill(self.ui.COLORS['OVERLAY_DARK'])
        header_overlay.set_alpha(160)  # Lighter for video visibility
        self.screen.blit(header_overlay, (header_rect[0], header_rect[1]))

        # Main title
        title_y = 25
        self.ui.draw_text_with_shadow(
            "Shmegl's Slayers",
            self.font_title,
            self.ui.COLORS['LIGHT_PURPLE'],
            (self.DISPLAY_SIZE[0]//2 - self.font_title.size("Shmegl's Slayers")[0]//2, title_y),
            self.ui.COLORS['OFF_BLACK'],
            (3, 3)
        )

        # Subtitle
        subtitle_y = title_y + 80
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

        # Leaderboard title with icons
        scores_title_y = content_y + self.ui.LAYOUT['PADDING']
        self.ui.draw_text_with_shadow(
            "🏆 TOP SCORES 🏆",
            self.font_large,
            self.ui.COLORS['GOLD_PURPLE'],
            (scores_section_x + scores_section_width//2 - self.font_large.size("🏆 TOP SCORES 🏆")[0]//2, scores_title_y),
            self.ui.COLORS['OFF_BLACK']
        )

        # Score entries
        scores = self.get_top_scores(8)  # Show top 8 for clean layout
        scores_start_y = scores_title_y + 60
        line_height = 50

        for i, (player_name, score) in enumerate(scores):
            entry_y = scores_start_y + i * line_height
            
            # Rank colors with purple theme and icons
            if i == 0:
                rank_color = self.ui.COLORS['GOLD_PURPLE']
                name_color = self.ui.COLORS['GOLD_PURPLE']
                icon = "👑"
            elif i == 1:
                rank_color = self.ui.COLORS['LIGHT_PURPLE']
                name_color = self.ui.COLORS['LIGHT_PURPLE']
                icon = "🥈"
            elif i == 2:
                rank_color = self.ui.COLORS['WARNING_PURPLE']
                name_color = self.ui.COLORS['WARNING_PURPLE']
                icon = "🥉"
            else:
                rank_color = self.ui.COLORS['MEDIUM_GRAY']
                name_color = self.ui.COLORS['OFF_WHITE']
                icon = "💀"  # Doom-themed icon for other entries

            # Icon
            self.ui.draw_text_with_shadow(
                icon,
                self.font_medium,
                rank_color,
                (scores_section_x + 15, entry_y),
                self.ui.COLORS['OFF_BLACK']
            )

            # Rank number
            rank_text = f"{i+1}."
            self.ui.draw_text_with_shadow(
                rank_text,
                self.font_medium,
                rank_color,
                (scores_section_x + 55, entry_y),
                self.ui.COLORS['OFF_BLACK']
            )

            # Player name (truncate if too long)
            display_name = player_name[:15] + "..." if len(player_name) > 15 else player_name
            self.ui.draw_text_with_shadow(
                display_name,
                self.font_medium,
                name_color,
                (scores_section_x + 105, entry_y),
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
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_F11:
                            pygame.display.toggle_fullscreen()

                # Draw main screen
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
        
        if hasattr(self, 'video_cap') and self.video_cap:
            self.video_cap.release()
            logger.info("Video capture released")
        
        pygame.quit()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    try:
        kiosk = DoomBoxKiosk()
        kiosk.run()
    except Exception as e:
        logger.error(f"Failed to start kiosk: {e}")
        sys.exit(1)