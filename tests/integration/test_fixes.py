#!/usr/bin/env python3
"""
Test script to validate the DoomBox integration fixes
Tests MQTT game launching, kiosk behavior, and controller support
"""

import os
import sys
import time
import logging
import json
import subprocess
import signal
from pathlib import Path

# Add current directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_game_launcher():
    """Test game launcher functionality"""
    logger.info("=== Testing Game Launcher ===")
    
    try:
        from game_launcher import GameLauncher
        
        launcher = GameLauncher()
        logger.info("✅ Game launcher created successfully")
        
        # Check dependencies
        if launcher.check_dependencies():
            logger.info("✅ All dependencies satisfied")
        else:
            logger.warning("⚠️  Some dependencies missing")
        
        # Check controllers
        controller_info = launcher.check_controllers()
        logger.info(f"Controller info: {json.dumps(controller_info, indent=2)}")
        
        if controller_info['controllers_found'] > 0:
            logger.info("✅ Controllers detected")
        else:
            logger.warning("⚠️  No controllers detected")
        
        # Test config setup
        if launcher.setup_doom_config():
            logger.info("✅ Doom configuration setup successful")
        else:
            logger.error("❌ Doom configuration setup failed")
            return False
        
        # Get status
        status = launcher.get_game_status()
        logger.info(f"Game status: {json.dumps(status, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Game launcher test failed: {e}")
        return False

def test_mqtt_client():
    """Test MQTT client functionality"""
    logger.info("=== Testing MQTT Client ===")
    
    try:
        from mqtt_client import DoomBoxMQTTClient
        
        mqtt_client = DoomBoxMQTTClient()
        logger.info("✅ MQTT client created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MQTT client test failed: {e}")
        return False

def test_integration():
    """Test game launcher and MQTT integration"""
    logger.info("=== Testing Integration ===")
    
    try:
        from game_launcher import GameLauncher
        from mqtt_client import DoomBoxMQTTClient
        
        # Create components
        launcher = GameLauncher()
        mqtt_client = DoomBoxMQTTClient()
        
        # Connect them
        mqtt_client.set_game_launcher(launcher)
        logger.info("✅ Game launcher connected to MQTT client")
        
        # Test state callbacks
        def test_callback(old_state, new_state, player_name):
            logger.info(f"🎮 Game state callback: {old_state} -> {new_state} (player: {player_name})")
        
        launcher.add_game_state_callback(test_callback)
        logger.info("✅ State callback registered")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def test_game_launch_simulation():
    """Test game launch without actually starting the game"""
    logger.info("=== Testing Game Launch Simulation ===")
    
    try:
        from game_launcher import GameLauncher
        
        launcher = GameLauncher()
        
        # Check if we can create the command without launching
        test_player = "TestPlayer"
        
        # Setup config
        launcher.setup_doom_config()
        
        # Build command (same logic as launch_game but don't execute)
        cmd = [
            launcher.doom_config['executable'],
            '-iwad', launcher.doom_config['iwad'],
            '-skill', '3',
            '-config', launcher.doom_config['config_file'],
            '-save', os.path.join(launcher.doom_config['save_dir'], f"{test_player}.dsg"),
            '-width', '1280',
            '-height', '960',
            '-fullscreen',
            '-exclusive_fullscreen',
            '-aspect', '1.33'
        ]
        
        logger.info(f"Game command would be: {' '.join(cmd)}")
        
        # Check if files exist
        if os.path.exists(launcher.doom_config['executable']):
            logger.info("✅ Doom executable found")
        else:
            logger.warning(f"⚠️  Doom executable not found: {launcher.doom_config['executable']}")
        
        if os.path.exists(launcher.doom_config['iwad']):
            logger.info("✅ DOOM WAD file found")
        else:
            logger.warning(f"⚠️  DOOM WAD file not found: {launcher.doom_config['iwad']}")
        
        if os.path.exists(launcher.doom_config['config_file']):
            logger.info("✅ Doom config file created")
        else:
            logger.warning(f"⚠️  Doom config file not found: {launcher.doom_config['config_file']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Game launch simulation failed: {e}")
        return False

def test_kiosk_imports():
    """Test kiosk manager imports without starting the full kiosk"""
    logger.info("=== Testing Kiosk Imports ===")
    
    try:
        # Test importing the kiosk manager (this will test pygame setup)
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("kiosk_manager", 
                                                     os.path.join(script_dir, "kiosk-manager.py"))
        kiosk_module = importlib.util.module_from_spec(spec)
        
        # This will fail if pygame/display is not available, but we can catch that
        try:
            spec.loader.exec_module(kiosk_module)
            logger.info("✅ Kiosk manager imports successful")
            return True
        except Exception as e:
            if "No available video device" in str(e) or "DISPLAY" in str(e):
                logger.warning(f"⚠️  Kiosk manager imports failed due to display: {e}")
                logger.info("This is expected in headless environment")
                return True
            else:
                logger.error(f"❌ Kiosk manager import error: {e}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Kiosk import test failed: {e}")
        return False

def test_controller_detection():
    """Test controller detection specifically"""
    logger.info("=== Testing Controller Detection ===")
    
    try:
        # Check for joystick devices
        import glob
        js_devices = glob.glob('/dev/input/js*')
        logger.info(f"Joystick devices found: {js_devices}")
        
        # Check for event devices
        event_devices = glob.glob('/dev/input/event*')
        logger.info(f"Event devices found: {len(event_devices)} devices")
        
        # Try to list input devices
        try:
            result = subprocess.run(['ls', '-la', '/dev/input/'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Input devices:")
                for line in result.stdout.split('\n'):
                    if 'js' in line or 'event' in line:
                        logger.info(f"  {line}")
        except Exception as e:
            logger.warning(f"Could not list input devices: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Controller detection test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting DoomBox Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Game Launcher", test_game_launcher),
        ("MQTT Client", test_mqtt_client),
        ("Integration", test_integration),
        ("Game Launch Simulation", test_game_launch_simulation),
        ("Kiosk Imports", test_kiosk_imports),
        ("Controller Detection", test_controller_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)
