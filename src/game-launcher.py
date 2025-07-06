#!/usr/bin/env python3
"""
DoomBox Game Launcher
Handles launching dsda-doom with proper configuration
Prepares for MQTT integration for remote game launching
"""

import os
import sys
import subprocess
import signal
import time
import logging
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

# Set up logging
script_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(script_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'game-launcher.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GameLauncher:
    """Handles launching and managing Doom games"""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.script_dir)  # Parent directory
        self.config_dir = os.path.join(self.base_dir, 'config')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.db_path = os.path.join(self.base_dir, 'doombox_scores.db')
        
        # Game process
        self.game_process = None
        self.current_player = None
        
        # Doom configuration
        self.doom_config = {
            'executable': self._find_doom_executable(),
            'iwad': '/usr/share/games/doom/doom1.wad',  # Shareware DOOM
            'resolution': '640x480',
            'skill': '3',  # Hurt Me Plenty
            'config_file': '/root/.dsda-doom/dsda-doom.cfg',
            'demo_dir': os.path.join(self.base_dir, 'demos'),
            'save_dir': os.path.join(self.base_dir, 'saves')
        }
        
        # Create directories
        for directory in [self.config_dir, self.logs_dir, self.doom_config['demo_dir'], self.doom_config['save_dir']]:
            os.makedirs(directory, exist_ok=True)
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize database
        self.setup_database()
        
        logger.info("GameLauncher initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_game()
        sys.exit(0)
    
    def _find_doom_executable(self) -> str:
        """Find dsda-doom executable in common locations"""
        possible_paths = [
            '/usr/games/dsda-doom',
            '/usr/local/games/dsda-doom',
            '/usr/bin/dsda-doom',
            '/usr/local/bin/dsda-doom'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found dsda-doom at: {path}")
                return path
        
        # Check if it's in PATH
        try:
            result = subprocess.run(['which', 'dsda-doom'], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.info(f"Found dsda-doom in PATH: {path}")
                return path
        except:
            pass
        
        logger.error("dsda-doom not found in any common locations")
        return '/usr/games/dsda-doom'  # fallback to common location
    
    def setup_database(self):
        """Initialize the scores database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create scores table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create game sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    event TEXT NOT NULL,
                    exit_code INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database setup error: {e}")
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        try:
            # Check for dsda-doom executable
            doom_exe = self.doom_config['executable']
            if not os.path.exists(doom_exe) and doom_exe != 'dsda-doom':
                logger.error(f"dsda-doom not found at {doom_exe}")
                return False
            elif doom_exe == 'dsda-doom':
                # Check if it's in PATH
                result = subprocess.run(['which', 'dsda-doom'], capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error("dsda-doom not found in PATH. Please install dsda-doom package.")
                    return False
            
            # Check for DOOM WAD file
            if not os.path.exists(self.doom_config['iwad']):
                logger.error(f"DOOM WAD file not found at {self.doom_config['iwad']}")
                logger.error("Please install doom-wad-shareware package.")
                return False
            
            logger.info("All dependencies satisfied")
            return True
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False
    
    def setup_doom_config(self) -> bool:
        """Setup dsda-doom configuration"""
        try:
            config_dir = os.path.dirname(self.doom_config['config_file'])
            os.makedirs(config_dir, exist_ok=True)
            
            # Basic dsda-doom configuration with controller support
            config_content = """# DoomBox dsda-doom configuration
use_joystick 1
joy_left 0
joy_right 1
joy_up 2
joy_down 3
joy_fire 4
joy_use 5
joy_run 6
joy_strafe 7
joy_menu 8
joy_weapon_next 9
joy_weapon_prev 10

# Video settings
screen_width 640
screen_height 480
use_fullscreen 1
render_vsync 1

# Audio settings
snd_sfxvolume 8
snd_musicvolume 4

# Game settings
default_skill 3
autorun 1
mouse_sensitivity 5

# Save settings
save_dir """ + self.doom_config['save_dir'] + """
demo_dir """ + self.doom_config['demo_dir'] + """
"""
            
            with open(self.doom_config['config_file'], 'w') as f:
                f.write(config_content)
            
            logger.info("dsda-doom configuration created")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Doom config: {e}")
            return False
    
    def launch_game(self, player_name: str, skill: int = 3) -> bool:
        """Launch Doom game for a player"""
        try:
            if self.game_process and self.game_process.poll() is None:
                logger.warning("Game is already running")
                return False
            
            self.current_player = player_name
            
            # Build command line arguments
            cmd = [
                self.doom_config['executable'],
                '-iwad', self.doom_config['iwad'],
                '-skill', str(skill),
                '-config', self.doom_config['config_file'],
                '-save', os.path.join(self.doom_config['save_dir'], f"{player_name}.dsg"),
                '-width', '640',
                '-height', '480',
                '-fullscreen'
            ]
            
            logger.info(f"Launching game for player: {player_name}")
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Launch the game
            self.game_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Log the game start
            self.log_game_session(player_name, 'started')
            
            logger.info(f"Game launched for {player_name} (PID: {self.game_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error launching game: {e}")
            return False
    
    def stop_game(self) -> bool:
        """Stop the current game"""
        try:
            if self.game_process and self.game_process.poll() is None:
                logger.info("Stopping game...")
                self.game_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.game_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Game didn't stop gracefully, forcing termination")
                    self.game_process.kill()
                    self.game_process.wait()
                
                # Log the game end
                if self.current_player:
                    self.log_game_session(self.current_player, 'stopped')
                
                logger.info("Game stopped")
                return True
            else:
                logger.info("No game running")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping game: {e}")
            return False
    
    def is_game_running(self) -> bool:
        """Check if a game is currently running"""
        return self.game_process and self.game_process.poll() is None
    
    def wait_for_game(self) -> Optional[int]:
        """Wait for the current game to finish and return exit code"""
        if not self.game_process:
            return None
        
        try:
            exit_code = self.game_process.wait()
            logger.info(f"Game finished with exit code: {exit_code}")
            
            # Log the game end
            if self.current_player:
                self.log_game_session(self.current_player, 'finished', exit_code)
            
            return exit_code
            
        except Exception as e:
            logger.error(f"Error waiting for game: {e}")
            return None
    
    def log_game_session(self, player_name: str, event: str, exit_code: Optional[int] = None):
        """Log game session events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create game_sessions table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    event TEXT NOT NULL,
                    exit_code INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert session event
            cursor.execute('''
                INSERT INTO game_sessions (player_name, event, exit_code)
                VALUES (?, ?, ?)
            ''', (player_name, event, exit_code))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging game session: {e}")
    
    def get_game_status(self) -> Dict[str, Any]:
        """Get current game status"""
        status = {
            'running': self.is_game_running(),
            'current_player': self.current_player,
            'process_id': self.game_process.pid if self.game_process else None,
            'doom_config': self.doom_config
        }
        return status

def main():
    """Main function for testing game launcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DoomBox Game Launcher')
    parser.add_argument('--launch', type=str, help='Launch game for player name')
    parser.add_argument('--skill', type=int, default=3, help='Skill level (1-5)')
    parser.add_argument('--stop', action='store_true', help='Stop current game')
    parser.add_argument('--status', action='store_true', help='Show game status')
    parser.add_argument('--wait', action='store_true', help='Wait for game to finish')
    parser.add_argument('--test', action='store_true', help='Test game launcher')
    
    args = parser.parse_args()
    
    launcher = GameLauncher()
    
    try:
        if args.test:
            print("Testing game launcher...")
            if launcher.check_dependencies():
                print("✓ Dependencies satisfied")
            else:
                print("✗ Missing dependencies")
                return 1
            
            if launcher.setup_doom_config():
                print("✓ Doom configuration setup")
            else:
                print("✗ Doom configuration failed")
                return 1
            
            print("Game launcher test completed")
            
        elif args.launch:
            if not launcher.check_dependencies():
                print("Missing dependencies")
                return 1
            
            launcher.setup_doom_config()
            
            if launcher.launch_game(args.launch, args.skill):
                print(f"Game launched for {args.launch}")
                
                if args.wait:
                    print("Waiting for game to finish...")
                    exit_code = launcher.wait_for_game()
                    print(f"Game finished with exit code: {exit_code}")
            else:
                print("Failed to launch game")
                return 1
        
        elif args.stop:
            if launcher.stop_game():
                print("Game stopped")
            else:
                print("No game running")
        
        elif args.status:
            status = launcher.get_game_status()
            print(json.dumps(status, indent=2))
        
        else:
            print("No action specified. Use --help for options.")
    
    except KeyboardInterrupt:
        print("\nGame launcher interrupted")
        launcher.stop_game()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
