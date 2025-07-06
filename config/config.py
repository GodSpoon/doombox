"""
DoomBox Configuration File - Optimized for Radxa Zero
Simplified and optimized for ARM hardware
"""

import os

# Display Settings - Optimized for Radxa Zero
DISPLAY_SIZE = (1280, 960)
DOOM_RESOLUTION = (640, 480)
FULLSCREEN = True
FPS_LIMIT = 30  # Reduced for ARM processor

# Kiosk Text
TITLE = "shmegl's DoomBox"
SUBTITLE = "Highest score gets a free tattoo!"
INSTRUCTION = "SCAN THE QR CODE TO ENTER THE BATTLE"
QR_LABEL = ">> SCAN TO PLAY <<"

# URLs and Integration
GITHUB_FORM_URL = "http://shmeglsdoombox.spoon.rip"
WEBHOOK_URL = "http://your-server:5000/register"  # Optional
INSTAGRAM_HANDLE = "@shmegl"

# Color Palette - Simplified for better performance
COLORS = {
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
    'LIGHT_GRAY': (192, 192, 192),
    'ORANGE': (255, 165, 0),
    'PURPLE': (128, 0, 128),
    'PINK': (255, 192, 203),
    'BROWN': (165, 42, 42),
    'LIME': (0, 255, 0),
}

# Animation Settings - Reduced for performance
TITLE_PULSE_SPEED = 0.05  # Slower for ARM
ANIMATION_ENABLED = True
EFFECTS_ENABLED = False  # Disable heavy effects on ARM

# UI Layout Settings
QR_CODE_SIZE = 300
QR_CODE_POSITION = (150, 300)
QR_BORDER_SIZE = 4

SCORES_PANEL_POSITION = (550, 300)
SCORES_PANEL_SIZE = (600, 400)
MAX_SCORES_DISPLAYED = 10

# Typography Settings - Optimized fonts
FONT_SIZES = {
    'TITLE': 96,       # Reduced from 120
    'SUBTITLE': 64,    # Reduced from 72
    'HEADER': 48,      # Headers
    'CONTENT': 32,     # Main content
    'FOOTER': 24,      # Footer text
    'TINY': 18,        # Very small text
}

# Score Display Colors
SCORE_COLORS = {
    'FIRST_PLACE': 'YELLOW',      # Gold
    'SECOND_PLACE': 'LIGHT_GRAY', # Silver  
    'THIRD_PLACE': 'ORANGE',      # Bronze
    'OTHER_PLACES': 'WHITE',      # Regular
    'NO_SCORES': 'GRAY',          # When empty
}

# Status Colors
STATUS_COLORS = {
    'CONTROLLER_ONLINE': 'GREEN',
    'CONTROLLER_OFFLINE': 'RED',
    'GAME_RUNNING': 'CYAN',
    'WAITING': 'YELLOW',
    'ERROR': 'RED',
}

# MQTT Settings
MQTT_ENABLED = True
MQTT_BROKER = "10.0.0.215"  # Your Arch host IP - update this to match your actual IP
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_TOPICS = {
    'commands': 'doombox/commands',
    'status': 'doombox/status',
    'scores': 'doombox/scores',
    'players': 'doombox/players',
    'system': 'doombox/system',
    'start_game': 'doombox/start_game'  # For web form compatibility
}

# Controller Settings
CONTROLLER_NAME = "Sony Interactive Entertainment Wireless Controller"  # PS4 Controller
AUTO_RECONNECT = True
CONTROLLER_CHECK_INTERVAL = 5  # seconds

# Konami Code (simplified button mapping)
KONAMI_SEQUENCE = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
KONAMI_TIMEOUT = 5.0  # seconds

# Game Settings
DOOM_EXECUTABLE = "/usr/local/bin/lzdoom"  # Our compatibility wrapper
DOOM_WAD_PATH = "/opt/doombox/doom/DOOM.WAD"
DOOM_EXTRA_ARGS = [
    "-width", str(DOOM_RESOLUTION[0]),
    "-height", str(DOOM_RESOLUTION[1]),
    "-fullscreen" if FULLSCREEN else "-windowed",
    "-nomusic",  # Disable music for better performance
    "-nosound"   # Disable sound for better performance (comment out if you want audio)
]

# File Paths
BASE_DIR = "/opt/doombox"
LOGS_DIR = f"{BASE_DIR}/logs"
TRIGGER_FILE = f"{BASE_DIR}/new_player.json"
SCORE_DATABASE = f"{BASE_DIR}/scores.db"
DOOM_DIR = f"{BASE_DIR}/doom"

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = f"{LOGS_DIR}/doombox.log"
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB (reduced for ARM storage)
LOG_BACKUP_COUNT = 3

# Feature Flags
ENABLE_MQTT = True
ENABLE_FILE_TRIGGER = True
ENABLE_WEBHOOK_CHECK = False
ENABLE_CONTROLLER = True
ENABLE_KONAMI_CODE = True
ENABLE_TEST_MODE = True
ENABLE_EFFECTS = False  # Disable heavy visual effects

# Performance Settings - Optimized for ARM
PYGAME_BUFFER_SIZE = 256  # Reduced buffer
AUDIO_ENABLED = False     # Disable audio for better performance
VSYNC_ENABLED = False     # Disable VSYNC for ARM
RENDER_SCALE = 1.0        # No scaling for better performance

# Timing Settings
QR_CODE_REFRESH_INTERVAL = 300  # 5 minutes
SCORE_DISPLAY_DURATION = 10
GAME_START_DELAY = 2
INPUT_POLLING_RATE = 1/30  # 30 FPS
FILE_CHECK_INTERVAL = 1    # Check trigger file every second

# Test Mode Settings
TEST_PLAYER_PREFIX = "TEST_"
TEST_SCORES_IN_DATABASE = False
DEMO_SCORE_RANGE = (100, 9999)

# Network Settings
NETWORK_TIMEOUT = 10  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# Hardware-Specific Settings (Radxa Zero)
ARM_OPTIMIZATIONS = True
GPU_MEMORY_SPLIT = 64    # MB for GPU (reduced)
DISABLE_COMPOSITING = True
FORCE_SOFTWARE_RENDER = False

# QR Code Settings
QR_CODE_SETTINGS = {
    'VERSION': 2,         # Smaller QR code for performance
    'ERROR_CORRECTION': 'L',  # Low error correction for smaller size
    'BOX_SIZE': 8,        # Reduced box size
    'BORDER': 4,          # Reduced border
    'FILL_COLOR': 'white',
    'BACK_COLOR': 'black',
}

# Database Settings
DB_TIMEOUT = 30  # seconds
DB_RETRY_ATTEMPTS = 3
AUTO_VACUUM = True

# Security Settings
SANITIZE_PLAYER_NAMES = True
MAX_PLAYER_NAME_LENGTH = 20
ALLOWED_NAME_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

# Messages
MESSAGES = {
    'GAME_STARTING': ">>> STARTING DOOM FOR {player_name} <<<",
    'GAME_ENDED': "GAME OVER! FINAL SCORE: {score}",
    'NEW_HIGH_SCORE': "*** NEW HIGH SCORE! ***",
    'CONTROLLER_DISCONNECTED': "CONTROLLER OFFLINE - PLEASE RECONNECT",
    'WAITING_FOR_PLAYERS': "AWAITING WARRIORS...",
    'KONAMI_ACTIVATED': "*** TEST MODE ACTIVATED ***",
    'ERROR': "SYSTEM ERROR - PLEASE TRY AGAIN",
    'NO_SCORES': "NO SCORES YET - BE THE FIRST!",
    'SCAN_TO_PLAY': ">> SCAN TO ENTER <<",
    'NOW_PLAYING': ">>> NOW PLAYING: {player_name} <<<",
}

# Version Information
VERSION = "2.1.0"
VERSION_CODENAME = "ARM OPTIMIZED"
BUILD_DATE = "2025-07-06"
AUTHOR = "shmegl"

# Development/Debug Settings
DEBUG_MODE = False
SHOW_FPS = False
VERBOSE_LOGGING = False
SIMULATE_SCORES = False

# Backup Settings
AUTO_BACKUP_SCORES = True
BACKUP_INTERVAL_HOURS = 24
BACKUP_RETENTION_DAYS = 7  # Reduced for ARM storage
BACKUP_LOCATION = f"{BASE_DIR}/backups"

# Helper functions
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        BASE_DIR,
        LOGS_DIR,
        DOOM_DIR,
        BACKUP_LOCATION
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def get_display_info():
    """Get display information for debugging"""
    import pygame
    pygame.init()
    return {
        'driver': pygame.display.get_driver(),
        'modes': pygame.display.list_modes(),
        'current_mode': pygame.display.get_surface().get_size() if pygame.display.get_surface() else None
    }

def get_system_info():
    """Get system information for debugging"""
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'processor': platform.processor(),
        'memory': f"{psutil.virtual_memory().total // (1024**3)}GB",
        'cpu_count': psutil.cpu_count(),
        'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }

# Validation
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check required files
    if not os.path.exists(DOOM_WAD_PATH):
        errors.append(f"DOOM.WAD not found at {DOOM_WAD_PATH}")
    
    if not os.path.exists(DOOM_EXECUTABLE):
        errors.append(f"DOOM executable not found at {DOOM_EXECUTABLE}")
    
    # Check directories
    try:
        ensure_directories()
    except Exception as e:
        errors.append(f"Cannot create directories: {e}")
    
    # Check display settings
    if DISPLAY_SIZE[0] < 800 or DISPLAY_SIZE[1] < 600:
        errors.append("Display size too small")
    
    return errors

# Auto-run validation if imported
if __name__ != "__main__":
    ensure_directories()