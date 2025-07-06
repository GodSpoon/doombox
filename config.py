"""
DoomBox Retro Configuration File
Enhanced settings for the retro aesthetic kiosk
"""

# Display Settings
DISPLAY_SIZE = (1280, 960)
DOOM_RESOLUTION = (640, 480)
FULLSCREEN = True
FPS_LIMIT = 60  # Higher FPS for smooth animations

# Kiosk Text - Enhanced for retro feel
TITLE = "shmegl's DoomBox"
SUBTITLE = "Highest score gets a free tattoo!"
INSTRUCTION = "SCAN THE QR CODE TO ENTER THE BATTLE"
QR_LABEL = ">> SCAN TO ENTER <<"

# URLs and Integration - Updated URL
GITHUB_FORM_URL = "http://shmeglsdoombox.spoon.rip"
WEBHOOK_URL = "http://your-server:5000/register"  # Optional
INSTAGRAM_HANDLE = "@shmegl"

# Retro Color Palette - Classic arcade machine colors
RETRO_COLORS = {
    # Base colors
    'BLACK': (0, 0, 0),
    'DARK_GRAY': (32, 32, 32),
    'GRAY': (64, 64, 64),
    'LIGHT_GRAY': (128, 128, 128),
    'WHITE': (255, 255, 255),
    
    # Bright primary colors
    'BRIGHT_RED': (255, 0, 0),
    'BRIGHT_GREEN': (0, 255, 0),
    'BRIGHT_BLUE': (0, 0, 255),
    'BRIGHT_YELLOW': (255, 255, 0),
    'BRIGHT_CYAN': (0, 255, 255),
    'BRIGHT_MAGENTA': (255, 0, 255),
    
    # Dark variants
    'DARK_RED': (128, 0, 0),
    'DARK_GREEN': (0, 128, 0),
    'DARK_BLUE': (0, 0, 128),
    
    # Special colors
    'ORANGE': (255, 128, 0),
    'PURPLE': (128, 0, 255),
    'LIME': (128, 255, 0),
    'PINK': (255, 128, 255),
    'TEAL': (0, 128, 128),
    'AMBER': (255, 191, 0),
    'BLOOD_RED': (139, 0, 0),
    
    # CRT monitor colors
    'CRT_GREEN': (0, 255, 0),
    'CRT_AMBER': (255, 176, 0),
    'CRT_WHITE': (192, 192, 192),
}

# Animation Settings
TITLE_PULSE_SPEED = 0.1
SUBTITLE_COLOR_CYCLE_SPEED = 30  # frames
BORDER_COLOR_CYCLE_SPEED = 20   # frames
QR_LABEL_PULSE_SPEED = 0.2

# UI Layout Settings
QR_CODE_SIZE = 400
QR_CODE_POSITION = (100, 280)
QR_BORDER_SIZE = 8
QR_FRAME_PADDING = 20

SCORES_PANEL_POSITION = (600, 280)
SCORES_PANEL_SIZE = (600, 480)
MAX_SCORES_DISPLAYED = 10

# Typography Settings
FONT_SIZES = {
    'TITLE': 120,      # Main title
    'SUBTITLE': 72,    # Subtitle  
    'HEADER': 48,      # Section headers
    'CONTENT': 32,     # Main content
    'FOOTER': 24,      # Footer text
    'TINY': 18,        # Very small text
}

# Visual Effects Settings
SCANLINES_ENABLED = True
SCANLINES_INTENSITY = 0.05

GLOW_EFFECTS_ENABLED = True
GLOW_RADIUS = 3

GRID_BACKGROUND_ENABLED = True
GRID_SIZE = 40

CRT_EFFECTS = {
    'SCANLINES': True,
    'GLOW': True,
    'GRID': True,
    'BORDER_ANIMATION': True,
}

# Score Display Colors
SCORE_COLORS = {
    'FIRST_PLACE': 'BRIGHT_YELLOW',   # Gold
    'SECOND_PLACE': 'LIGHT_GRAY',     # Silver  
    'THIRD_PLACE': 'ORANGE',          # Bronze
    'OTHER_PLACES': 'WHITE',          # Regular
    'NO_SCORES': 'GRAY',              # When empty
}

# Status Colors
STATUS_COLORS = {
    'CONTROLLER_ONLINE': 'BRIGHT_GREEN',
    'CONTROLLER_OFFLINE': 'BRIGHT_RED',
    'GAME_RUNNING': 'BRIGHT_WHITE',
    'WAITING': 'BRIGHT_CYAN',
    'ERROR': 'BRIGHT_RED',
}

# MQTT Settings (Optional)
MQTT_ENABLED = True
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "doombox/start_game"

# Controller Settings
CONTROLLER_NAME = "Sony Interactive Entertainment Wireless Controller"  # PS4 Controller
AUTO_RECONNECT = True

# Konami Code (controller button mapping)
KONAMI_BUTTONS = [
    'dpad_up', 'dpad_up', 'dpad_down', 'dpad_down',
    'dpad_left', 'dpad_right', 'dpad_left', 'dpad_right',
    'button_1', 'button_0'  # Circle, X (reversed for emphasis)
]

# Game Settings
DOOM_EXECUTABLE = "lzdoom"
DOOM_WAD_PATH = "/opt/doombox/doom/DOOM.WAD"
DOOM_EXTRA_ARGS = [
    "-width", str(DOOM_RESOLUTION[0]),
    "-height", str(DOOM_RESOLUTION[1]),
    "-fullscreen" if FULLSCREEN else "-windowed"
]

# File Paths
BASE_DIR = "/opt/doombox"
LOGS_DIR = f"{BASE_DIR}/logs"
TRIGGER_FILE = f"{BASE_DIR}/new_player.json"
SCORE_DATABASE = f"{BASE_DIR}/scores.db"

# Auto-start Settings
AUTO_START_ON_BOOT = True
AUTO_LOGIN_USER = "root"

# Security Settings (for production)
SANITIZE_PLAYER_NAMES = True
MAX_PLAYER_NAME_LENGTH = 20
ALLOWED_NAME_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = f"{LOGS_DIR}/doombox.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Feature Flags
ENABLE_MQTT = True
ENABLE_FILE_TRIGGER = True
ENABLE_WEBHOOK_CHECK = False
ENABLE_CONTROLLER = True
ENABLE_KONAMI_CODE = True
ENABLE_TEST_MODE = True
ENABLE_RETRO_EFFECTS = True

# Test Mode Settings
TEST_PLAYER_PREFIX = "TEST_"
TEST_SCORES_IN_DATABASE = False

# Timing Settings (seconds)
QR_CODE_REFRESH_INTERVAL = 300  # 5 minutes
SCORE_DISPLAY_DURATION = 10
CONTROLLER_CHECK_INTERVAL = 5
GAME_START_DELAY = 2
INPUT_POLLING_RATE = 1/60  # 60 FPS

# Prize Settings
PRIZE_DESCRIPTION = "free tattoo"
WINNER_NOTIFICATION = True
WINNER_DISPLAY_DURATION = 30  # seconds

# Advanced Retro Settings
PIXEL_PERFECT_RENDERING = True
CRISP_SCALING = True  # No interpolation for pixel art
RETRO_FONT_RENDERING = False  # Disable antialiasing for pixel fonts

# Custom Messages - Enhanced for retro feel
MESSAGES = {
    'GAME_STARTING': ">>> INITIATING DOOM PROTOCOL FOR {player_name} <<<",
    'GAME_ENDED': "GAME OVER! FINAL SCORE: {score}",
    'NEW_HIGH_SCORE': "🎉 *** NEW HIGH SCORE ACHIEVED *** 🎉",
    'CONTROLLER_DISCONNECTED': "CONTROLLER OFFLINE - PLEASE RECONNECT",
    'WAITING_FOR_PLAYERS': "AWAITING WARRIORS...",
    'KONAMI_ACTIVATED': "*** TEST MODE ACTIVATED ***",
    'ERROR': "SYSTEM ERROR - PLEASE TRY AGAIN",
    'NO_SCORES': "NO SCORES YET - BE THE FIRST!",
    'SCAN_TO_PLAY': ">> SCAN TO ENTER <<",
    'NOW_PLAYING': ">>> NOW PLAYING: {player_name} <<<",
}

# Network Settings
NETWORK_TIMEOUT = 10  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# Performance Settings
PYGAME_BUFFER_SIZE = 512
AUDIO_ENABLED = True
VSYNC_ENABLED = True

# Development/Debug Settings
DEBUG_MODE = False
SHOW_FPS = False
VERBOSE_LOGGING = False
SIMULATE_SCORES = False  # Generate random scores for testing

# Backup Settings
AUTO_BACKUP_SCORES = True
BACKUP_INTERVAL_HOURS = 24
BACKUP_RETENTION_DAYS = 30
BACKUP_LOCATION = f"{BASE_DIR}/backups"

# Hardware-Specific Settings (Radxa Zero)
GPU_MEMORY_SPLIT = 128  # MB for GPU
CPU_GOVERNOR = "performance"  # performance, powersave, ondemand
DISABLE_WIFI_POWER_SAVE = True

# Additional DOOM Settings
DOOM_SKILL_LEVEL = 3  # 1=ITYTD, 2=HNTR, 3=HMP, 4=UV, 5=NM
DOOM_START_LEVEL = 1  # E1M1
DOOM_EPISODE = 1
DOOM_MUSIC_ENABLED = True
DOOM_SOUND_ENABLED = True
DOOM_MONSTERS_ENABLED = True

# Custom DOOM Parameters (advanced users)
CUSTOM_DOOM_ARGS = [
    # Example custom arguments:
    # "+sv_cheats", "0",
    # "+dmflags", "0",
    # "+skill", str(DOOM_SKILL_LEVEL)
]

# Retro Theme Presets
THEME_PRESETS = {
    'CLASSIC_ARCADE': {
        'PRIMARY': 'BRIGHT_RED',
        'SECONDARY': 'BRIGHT_YELLOW',
        'ACCENT': 'BRIGHT_GREEN',
        'BACKGROUND': 'BLACK',
        'TEXT': 'WHITE',
    },
    'CRT_GREEN': {
        'PRIMARY': 'CRT_GREEN',
        'SECONDARY': 'BRIGHT_GREEN',
        'ACCENT': 'LIME',
        'BACKGROUND': 'BLACK',
        'TEXT': 'CRT_GREEN',
    },
    'AMBER_TERMINAL': {
        'PRIMARY': 'CRT_AMBER',
        'SECONDARY': 'AMBER',
        'ACCENT': 'BRIGHT_YELLOW',
        'BACKGROUND': 'BLACK',
        'TEXT': 'CRT_AMBER',
    },
    'NEON_CYBERPUNK': {
        'PRIMARY': 'BRIGHT_MAGENTA',
        'SECONDARY': 'BRIGHT_CYAN',
        'ACCENT': 'BRIGHT_BLUE',
        'BACKGROUND': 'BLACK',
        'TEXT': 'WHITE',
    },
}

# Active theme
ACTIVE_THEME = 'CLASSIC_ARCADE'

# Border Animation Colors
BORDER_ANIMATION_COLORS = [
    'BRIGHT_RED',
    'BRIGHT_YELLOW', 
    'BRIGHT_GREEN',
    'BRIGHT_CYAN',
    'BRIGHT_BLUE',
    'BRIGHT_MAGENTA'
]

# QR Code Settings
QR_CODE_SETTINGS = {
    'VERSION': 3,  # Size of QR code (1-40, higher = larger)
    'ERROR_CORRECTION': 'L',  # L, M, Q, H (L = lowest, H = highest)
    'BOX_SIZE': 12,  # Size of each box in pixels
    'BORDER': 8,     # Border size around QR code
    'FILL_COLOR': 'WHITE',
    'BACK_COLOR': 'BLACK',
}

# Screen Saver Settings
SCREEN_SAVER_TIMEOUT = 0  # 0 = disabled
ATTRACT_MODE = False  # Show demo gameplay when idle
DEMO_TIMEOUT = 120  # seconds before starting demo

# Accessibility Settings
HIGH_CONTRAST_MODE = False
LARGE_TEXT_MODE = False
REDUCE_ANIMATIONS = False

# Easter Eggs
ENABLE_EASTER_EGGS = True
KONAMI_CODE_TIMEOUT = 5.0  # seconds

# Version Information
VERSION = "2.0.0"
VERSION_CODENAME = "RETRO EDITION"
BUILD_DATE = "2025-07-06"
AUTHOR = "shmegl"
