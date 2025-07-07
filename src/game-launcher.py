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
import threading
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
        
        # Game process and state
        self.game_process = None
        self.current_player = None
        self.game_state = "idle"  # idle, starting, running, finished
        self.game_state_callbacks = []
        
        # Game monitoring thread
        self.monitor_thread = None
        self.monitor_running = False
        
        # Doom configuration
        self.doom_config = {
            'executable': self._find_doom_executable(),
            'iwad': self._find_doom_wad(),
            'resolution': '1280x960',  # Match kiosk resolution
            'skill': '3',  # Hurt Me Plenty
            'config_file': os.path.join(self.base_dir, 'config', 'dsda-doom.cfg'),
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
    
    def add_game_state_callback(self, callback):
        """Add a callback to be called when game state changes"""
        self.game_state_callbacks.append(callback)
    
    def _notify_game_state_change(self, old_state, new_state):
        """Notify all callbacks of game state change"""
        for callback in self.game_state_callbacks:
            try:
                callback(old_state, new_state, self.current_player)
            except Exception as e:
                logger.error(f"Error in game state callback: {e}")
    
    def _set_game_state(self, state):
        """Set game state and notify callbacks"""
        old_state = self.game_state
        self.game_state = state
        if old_state != state:
            logger.info(f"Game state changed: {old_state} -> {state}")
            self._notify_game_state_change(old_state, state)
    
    def _monitor_game_process(self):
        """Monitor game process in background thread"""
        while self.monitor_running and self.game_process:
            try:
                # Check if process is still running
                if self.game_process.poll() is None:
                    # Game is still running
                    if self.game_state == "starting":
                        self._set_game_state("running")
                    time.sleep(1)
                else:
                    # Game has finished
                    exit_code = self.game_process.returncode
                    logger.info(f"Game process finished with exit code: {exit_code}")
                    
                    # Log the game end
                    if self.current_player:
                        self.log_game_session(self.current_player, 'finished', exit_code)
                    
                    self._set_game_state("finished")
                    
                    # Clean up
                    self.game_process = None
                    current_player = self.current_player
                    self.current_player = None
                    self.monitor_running = False
                    
                    # After a brief pause, set back to idle (this will restore kiosk)
                    time.sleep(3)  # Give a bit more time for cleanup
                    self._set_game_state("idle")
                    
                    logger.info(f"Game session ended for player: {current_player}")
                    break
                    
            except Exception as e:
                logger.error(f"Error monitoring game process: {e}")
                break
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_game()
        sys.exit(0)
    
    def _find_doom_executable(self) -> str:
        """Find dsda-doom executable in common locations"""
        possible_names = ['dsda-doom', 'prboom-plus', 'gzdoom', 'doom', 'freedoom']
        possible_paths = [
            '/usr/games/',
            '/usr/local/games/',
            '/usr/bin/',
            '/usr/local/bin/',
            '/opt/doom/',
            '/snap/bin/'
        ]
        
        # First check if any doom executable is in PATH
        for name in possible_names:
            try:
                result = subprocess.run(['which', name], capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    logger.info(f"Found {name} in PATH: {path}")
                    return path
            except:
                pass
        
        # Then check specific paths
        for path_dir in possible_paths:
            for name in possible_names:
                full_path = os.path.join(path_dir, name)
                if os.path.exists(full_path):
                    logger.info(f"Found {name} at: {full_path}")
                    return full_path
        
        logger.warning("No Doom executable found in any common locations")
        return 'dsda-doom'  # fallback - will be checked in dependencies
    
    def _find_doom_wad(self) -> str:
        """Find DOOM WAD file in common locations"""
        possible_wads = [
            # Shareware DOOM
            'doom1.wad', 'doom.wad', 'DOOM1.WAD', 'DOOM.WAD',
            # FreeDoom
            'freedoom1.wad', 'freedoom2.wad', 'freedm.wad',
            'FREEDOOM1.WAD', 'FREEDOOM2.WAD', 'FREEDM.WAD'
        ]
        
        possible_paths = [
            '/usr/share/games/doom/',
            '/usr/share/doom/',
            '/usr/local/share/doom/',
            '/opt/doom/',
            '/usr/share/freedoom/',
            '/usr/local/share/freedoom/',
            self.base_dir + '/doom/',  # Local doom directory
            self.base_dir + '/wads/'   # Local wads directory
        ]
        
        for path_dir in possible_paths:
            for wad in possible_wads:
                full_path = os.path.join(path_dir, wad)
                if os.path.exists(full_path):
                    logger.info(f"Found DOOM WAD at: {full_path}")
                    return full_path
        
        logger.warning("No DOOM WAD file found in any common locations")
        return '/usr/share/games/doom/doom1.wad'  # fallback
    
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
        """Setup dsda-doom configuration with enforced fullscreen mode and controller support"""
        try:
            config_dir = os.path.dirname(self.doom_config['config_file'])
            os.makedirs(config_dir, exist_ok=True)
            
            # Enhanced dsda-doom configuration with strong fullscreen enforcement and controller support
            config_content = """# DoomBox dsda-doom configuration - simplified for compatibility
# Controller/Joystick settings
use_joystick 1
joystick_index 0
joy_sensitivity 10

# Video settings - FULLSCREEN ONLY
screen_width 1280
screen_height 960
use_fullscreen 1
fullscreen 1
render_vsync 1

# Display settings
aspect_ratio 1.33

# Audio settings
snd_sfxvolume 8
snd_musicvolume 4

# Game settings
default_skill 3
autorun 1
mouse_sensitivity 5

# Performance settings
use_hardware_gamma 1

# Save settings
save_dir """ + self.doom_config['save_dir'] + """
demo_dir """ + self.doom_config['demo_dir'] + """
"""
            
            with open(self.doom_config['config_file'], 'w') as f:
                f.write(config_content)
            
            logger.info("dsda-doom configuration created with fullscreen enforcement and controller support")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Doom config: {e}")
            return False
    
    def launch_game(self, player_name: str, skill: int = 3) -> bool:
        """Launch Doom game for a player with fullscreen enforcement and controller support"""
        try:
            if self.game_process and self.game_process.poll() is None:
                logger.warning("Game is already running")
                return False
            
            self.current_player = player_name
            self._set_game_state("starting")
            
            # Check for controllers before launching
            controllers = self.check_controllers()
            logger.info(f"Controller status: {controllers['controllers_found']} controllers, {controllers['joysticks_found']} joystick devices")
            
            # Setup configuration before launching
            self.setup_doom_config()
            
            # Build command line arguments with enhanced fullscreen enforcement
            cmd = [
                self.doom_config['executable'],
                '-iwad', self.doom_config['iwad'],
                '-skill', str(skill),
                '-config', self.doom_config['config_file'],
                '-save', os.path.join(self.doom_config['save_dir'], f"{player_name}.dsg"),
                '-width', '1280',
                '-height', '960',
                '-fullscreen',
                '-aspect', '1.33'
            ]
            
            logger.info(f"Launching game for player: {player_name}")
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Enhanced environment for proper controller and display support + fullscreen enforcement
            game_env = dict(os.environ, **{
                'SDL_VIDEODRIVER': 'x11',
                'DISPLAY': ':0',
                'SDL_VIDEO_WINDOW_POS': '0,0',
                'SDL_VIDEO_CENTERED': '0',  # Don't center, use full screen
                'SDL_VIDEO_FULLSCREEN_HEAD': '0',  # Use first display
                'SDL_VIDEO_FULLSCREEN_DISPLAY': '0',  # Use display 0
                'SDL_VIDEO_ALLOW_SCREENSAVER': '0',  # Disable screensaver
                'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS': '1',
                'SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS': '1',
                # Force window manager to treat as fullscreen
                'SDL_VIDEO_X11_WMCLASS': 'dsda-doom',
                # Disable compositing for better performance
                'KWIN_TRIPLE_BUFFER': '0',
                'COMPIZ_OPTIONS': 'NO_EFFECTS'
            })
            
            # Brief delay to ensure kiosk has properly minimized and freed the display
            logger.info("Waiting for kiosk to fully minimize...")
            time.sleep(1)
            
            # Launch the game with priority to ensure it gets focus
            self.game_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=game_env,
                preexec_fn=os.setsid  # Create new session to prevent interference
            )
            
            # Log the game start
            self.log_game_session(player_name, 'started')
            
            # Start monitoring the game process
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_game_process, daemon=True)
            self.monitor_thread.start()
            
            logger.info(f"Game launched for {player_name} (PID: {self.game_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error launching game: {e}")
            self._set_game_state("idle")
            return False
    
    def stop_game(self) -> bool:
        """Stop the current game"""
        try:
            if self.game_process and self.game_process.poll() is None:
                logger.info("Stopping game...")
                
                # Stop monitoring thread
                self.monitor_running = False
                
                # Terminate the game process
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
                
                # Clean up
                self.game_process = None
                self.current_player = None
                self._set_game_state("idle")
                
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
    
    def check_controllers(self) -> Dict[str, Any]:
        """Check for available game controllers and joysticks"""
        controller_info = {
            'controllers_found': 0,
            'controllers': [],
            'joysticks_found': 0,
            'joysticks': []
        }
        
        try:
            # Check for joystick devices in /dev/input
            import glob
            js_devices = glob.glob('/dev/input/js*')
            controller_info['joysticks_found'] = len(js_devices)
            controller_info['joysticks'] = js_devices
            
            # Try to get more detailed info using pygame
            try:
                import pygame
                pygame.init()
                pygame.joystick.init()
                
                num_joysticks = pygame.joystick.get_count()
                controller_info['pygame_joysticks'] = num_joysticks
                
                for i in range(num_joysticks):
                    try:
                        joystick = pygame.joystick.Joystick(i)
                        joystick.init()
                        controller_info['controllers'].append({
                            'id': i,
                            'name': joystick.get_name(),
                            'axes': joystick.get_numaxes(),
                            'buttons': joystick.get_numbuttons(),
                            'hats': joystick.get_numhats()
                        })
                        controller_info['controllers_found'] += 1
                    except Exception as e:
                        logger.error(f"Error checking joystick {i}: {e}")
                
                pygame.quit()
                
            except ImportError:
                logger.warning("Pygame not available for controller detection")
            
            # Check SDL controller environment
            controller_info['sdl_env'] = {
                'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS': os.environ.get('SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'),
                'SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS': os.environ.get('SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS')
            }
            
            logger.info(f"Controller check: {controller_info['controllers_found']} controllers, {controller_info['joysticks_found']} joystick devices")
            
        except Exception as e:
            logger.error(f"Error checking controllers: {e}")
            controller_info['error'] = str(e)
        
        return controller_info

    def get_game_status(self) -> Dict[str, Any]:
        """Get current game status including controller info"""
        status = {
            'running': self.is_game_running(),
            'state': self.game_state,
            'current_player': self.current_player,
            'process_id': self.game_process.pid if self.game_process else None,
            'doom_config': self.doom_config,
            'controllers': self.check_controllers()
        }
        return status
    
    def get_game_state(self) -> str:
        """Get current game state"""
        return self.game_state

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
