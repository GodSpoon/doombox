"""
DoomBox Configuration File
Edit these settings to customize your kiosk
"""

# Display Settings
DISPLAY_SIZE = (1280, 960)
DOOM_RESOLUTION = (640, 480)
FULLSCREEN = True
FPS_LIMIT = 30

# Kiosk Text
TITLE = "shmegl's DoomBox"
SUBTITLE = "Highest score gets a free tattoo!"
INSTRUCTION = "Scan the QR code and fill out the form to play"

# URLs and Integration
GITHUB_FORM_URL = "https://your-username.github.io/doombox-form/"
WEBHOOK_URL = "http://your-server:5000/register"  # Optional
INSTAGRAM_HANDLE = "@shmegl"

# MQTT Settings (Optional)
MQTT_ENABLED = True
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "doombox/start_game"

# Controller Settings
CONTROLLER_NAME = "Sony Interactive Entertainment Wireless Controller"  # PS4 Controller
AUTO_RECONNECT = True

# Konami Code (controller button mapping)
# Standard PS4 controller mapping:
# 0=X, 1=Circle, 2=Square, 3=Triangle
# D-pad: up=hat(0,1), down=hat(0,-1), left=hat(-1,0), right=hat(1,0)
KONAMI_BUTTONS = [
    'up', 'up', 'down', 'down',
    'left', 'right', 'left', 'right',
    1, 0  # Circle, X
]

# Game Settings
DOOM_EXECUTABLE = "lzdoom"
DOOM_WAD_PATH = "/opt/doombox/doom/DOOM.WAD"
DOOM_EXTRA_ARGS = [
    "-width", str(DOOM_RESOLUTION[0]),
    "-height", str(DOOM_RESOLUTION[1]),
    "-fullscreen" if FULLSCREEN else "-windowed"
]

# Score Settings
MAX_SCORES_DISPLAYED = 10
SCORE_DATABASE = "/opt/doombox/scores.db"

# File Paths
BASE_DIR = "/opt/doombox"
LOGS_DIR = f"{BASE_DIR}/logs"
TRIGGER_FILE = f"{BASE_DIR}/new_player.json"

# Colors (RGB tuples)
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'CYAN': (0, 255, 255),
    'MAGENTA': (255, 0, 255),
    'ORANGE': (255, 165, 0),
    'PURPLE': (128, 0, 128)
}

# Font Sizes
FONT_SIZES = {
    'TITLE': 72,
    'SUBTITLE': 48,
    'INSTRUCTION': 32,
    'SCORES': 32,
    'STATUS': 36
}

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

# Test Mode Settings
TEST_PLAYER_PREFIX = "TEST_"
TEST_SCORES_IN_DATABASE = False

# Timing Settings (seconds)
QR_CODE_REFRESH_INTERVAL = 300  # 5 minutes
SCORE_DISPLAY_DURATION = 10
CONTROLLER_CHECK_INTERVAL = 5
GAME_START_DELAY = 2

# Prize Settings
PRIZE_DESCRIPTION = "free tattoo"
WINNER_NOTIFICATION = True
WINNER_DISPLAY_DURATION = 30  # seconds

# Advanced Settings
SCREEN_SAVER_TIMEOUT = 0  # 0 = disabled
ATTRACT_MODE = False  # Show demo gameplay when idle
DEMO_TIMEOUT = 120  # seconds before starting demo

# Custom Messages
MESSAGES = {
    'GAME_STARTING': "Starting game for {player_name}...",
    'GAME_ENDED': "Game over! Final score: {score}",
    'NEW_HIGH_SCORE': "🎉 NEW HIGH SCORE! 🎉",
    'CONTROLLER_DISCONNECTED': "Controller disconnected. Please reconnect.",
    'WAITING_FOR_PLAYERS': "Waiting for players...",
    'KONAMI_ACTIVATED': "Test mode activated!",
    'ERROR': "Something went wrong. Please try again."
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
