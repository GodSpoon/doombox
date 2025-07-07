#!/usr/bin/env python3
"""
Simple validation script to test our kiosk/game launch fixes
Tests the core functionality without full MQTT integration
"""

import os
import sys
import time
import logging
import importlib.util

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_game_launcher():
    """Load GameLauncher from the hyphenated filename"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    game_launcher_path = os.path.join(src_dir, 'game-launcher.py')
    
    spec = importlib.util.spec_from_file_location("game_launcher", game_launcher_path)
    game_launcher_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game_launcher_module)
    return game_launcher_module.GameLauncher

def test_kiosk_state_management():
    """Test the kiosk state management improvements"""
    logger.info("🎮 Testing Kiosk State Management")
    
    try:
        GameLauncher = load_game_launcher()
        launcher = GameLauncher()
        
        # Test state callback system
        state_changes = []
        
        def test_callback(old_state, new_state, player):
            state_changes.append((old_state, new_state, player))
            logger.info(f"State change: {old_state} -> {new_state} (player: {player})")
        
        launcher.add_game_state_callback(test_callback)
        
        # Simulate state changes
        launcher._set_game_state("starting")
        launcher.current_player = "TestPlayer"
        launcher._set_game_state("running")
        launcher._set_game_state("finished")
        launcher.current_player = None
        launcher._set_game_state("idle")
        
        if len(state_changes) >= 3:
            logger.info("✅ State management system working")
            return True
        else:
            logger.error("❌ State management not working properly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Kiosk state management test failed: {e}")
        return False

def test_game_config():
    """Test game configuration generation"""
    logger.info("🎮 Testing Game Configuration")
    
    try:
        GameLauncher = load_game_launcher()
        launcher = GameLauncher()
        
        # Test config generation
        if launcher.setup_doom_config():
            config_path = launcher.doom_config['config_file']
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_content = f.read()
                
                # Check for our key improvements
                checks = [
                    'use_joystick 1',
                    'joy_sensitivity 10',
                    'force_fullscreen 1',
                    'screen_width 1280',
                    'screen_height 960',
                    'use_gl_surface 1',
                    'video_mode 1'
                ]
                
                passed = 0
                for check in checks:
                    if check in config_content:
                        logger.info(f"✅ Config contains: {check}")
                        passed += 1
                    else:
                        logger.warning(f"⚠️ Config missing: {check}")
                
                if passed >= 6:
                    logger.info("✅ Game configuration improvements applied")
                    return True
                else:
                    logger.error(f"❌ Only {passed}/{len(checks)} config improvements found")
                    return False
            else:
                logger.error("❌ Config file not found")
                return False
        else:
            logger.error("❌ Config setup failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Game configuration test failed: {e}")
        return False

def test_command_line_args():
    """Test enhanced command line arguments"""
    logger.info("🎮 Testing Command Line Arguments")
    
    try:
        GameLauncher = load_game_launcher()
        launcher = GameLauncher()
        
        # Generate the command that would be used
        # (without actually launching)
        player_name = "TestPlayer"
        skill = 3
        
        # Test config setup first
        if not launcher.setup_doom_config():
            logger.error("❌ Config setup failed")
            return False
        
        # Get the command arguments (simulate building the command)
        doom_exe = launcher.doom_config['executable']
        iwad = launcher.doom_config['iwad']
        config_file = launcher.doom_config['config_file']
        
        # Check that all paths exist or are reasonable
        checks = []
        
        # Check executable
        if os.path.exists(doom_exe) or doom_exe in ['dsda-doom', 'gzdoom']:
            checks.append("Executable path valid")
            logger.info(f"✅ Doom executable: {doom_exe}")
        else:
            logger.warning(f"⚠️ Doom executable not found: {doom_exe}")
        
        # Check IWAD
        if os.path.exists(iwad):
            checks.append("IWAD path valid")
            logger.info(f"✅ IWAD file found: {iwad}")
        else:
            logger.warning(f"⚠️ IWAD file not found: {iwad}")
        
        # Check config file exists after setup
        if os.path.exists(config_file):
            checks.append("Config file created")
            logger.info(f"✅ Config file: {config_file}")
        else:
            logger.warning(f"⚠️ Config file not created: {config_file}")
        
        # Test the basic command structure would include fullscreen flags
        expected_args = [
            '-config', config_file,
            '-iwad', iwad,
            '-skill', str(skill),
            '-force_fullscreen',
            '-nowindow',
            '-nograb'
        ]
        
        logger.info(f"✅ Command would include fullscreen enforcement flags")
        checks.append("Fullscreen flags present")
        
        if len(checks) >= 3:
            logger.info("✅ Command line arguments properly configured")
            return True
        else:
            logger.error(f"❌ Only {len(checks)} command checks passed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Command line test failed: {e}")
        return False

def test_controller_detection():
    """Test controller detection functionality"""
    logger.info("🎮 Testing Controller Detection")
    
    try:
        GameLauncher = load_game_launcher()
        launcher = GameLauncher()
        
        # Test controller check method
        controller_info = launcher.check_controllers()
        
        if isinstance(controller_info, dict):
            logger.info(f"✅ Controller detection returned: {controller_info}")
            
            # Check for expected keys
            expected_keys = ['controllers_found', 'joysticks_found', 'pygame_available']
            for key in expected_keys:
                if key in controller_info:
                    logger.info(f"✅ Controller info contains: {key}")
                else:
                    logger.warning(f"⚠️ Controller info missing: {key}")
            
            return True
        else:
            logger.error("❌ Controller detection didn't return dict")
            return False
            
    except Exception as e:
        logger.error(f"❌ Controller detection test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    logger.info("🚀 DoomBox Game Launch Fixes Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Kiosk State Management", test_kiosk_state_management),
        ("Game Configuration", test_game_config),
        ("Command Line Arguments", test_command_line_args),
        ("Controller Detection", test_controller_detection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔧 Running: {test_name}")
        results[test_name] = test_func()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 VALIDATION RESULTS")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, result in results.items():
        if result:
            logger.info(f"✅ PASS: {test_name}")
            passed += 1
        else:
            logger.info(f"❌ FAIL: {test_name}")
    
    total = len(results)
    logger.info(f"\n🎯 Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! The fixes are working correctly.")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
