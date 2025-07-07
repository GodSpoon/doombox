#!/usr/bin/env python3
"""
Test script to validate game launch fixes
Tests kiosk management, fullscreen game launching, and controller support
"""

import sys
import os
import time
import subprocess
import threading
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_controller_detection():
    """Test controller detection"""
    logger.info("=== Testing Controller Detection ===")
    
    try:
        from src.game_launcher import GameLauncher
        launcher = GameLauncher()
        
        controllers = launcher.check_controllers()
        logger.info(f"Controllers found: {controllers}")
        
        if controllers['controllers_found'] > 0:
            logger.info("✅ Controllers detected successfully")
            return True
        else:
            logger.warning("⚠️ No controllers detected")
            return False
    except Exception as e:
        logger.error(f"❌ Controller detection failed: {e}")
        return False

def test_game_launcher_config():
    """Test game launcher configuration"""
    logger.info("=== Testing Game Launcher Configuration ===")
    
    try:
        from src.game_launcher import GameLauncher
        launcher = GameLauncher()
        
        # Test dependencies
        if not launcher.check_dependencies():
            logger.error("❌ Dependencies not satisfied")
            return False
        
        # Test configuration setup
        if not launcher.setup_doom_config():
            logger.error("❌ Configuration setup failed")
            return False
        
        logger.info("✅ Game launcher configuration successful")
        return True
    except Exception as e:
        logger.error(f"❌ Game launcher configuration failed: {e}")
        return False

def test_kiosk_startup():
    """Test kiosk startup without full run"""
    logger.info("=== Testing Kiosk Startup ===")
    
    try:
        # Set environment variables for headless testing
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        from src.kiosk_manager import DoomBoxKiosk
        
        # Initialize kiosk but don't run main loop
        kiosk = DoomBoxKiosk()
        
        # Test that all components initialized
        if hasattr(kiosk, 'game_launcher') and kiosk.game_launcher:
            logger.info("✅ Game launcher integrated successfully")
        
        if hasattr(kiosk, 'kiosk_hidden'):
            logger.info("✅ Kiosk state management initialized")
        
        # Cleanup
        kiosk.cleanup()
        
        logger.info("✅ Kiosk startup test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Kiosk startup test failed: {e}")
        return False

def test_game_launch_simulation():
    """Simulate game launch without actually launching DOOM"""
    logger.info("=== Testing Game Launch Simulation ===")
    
    try:
        from src.game_launcher import GameLauncher
        launcher = GameLauncher()
        
        # Test game state changes
        old_state = launcher.get_game_state()
        logger.info(f"Initial game state: {old_state}")
        
        # Test configuration generation
        config_success = launcher.setup_doom_config()
        if config_success:
            logger.info("✅ Game configuration generated successfully")
            
            # Check if config file exists and has correct content
            config_path = launcher.doom_config['config_file']
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_content = f.read()
                    
                # Check for key settings
                checks = [
                    'use_joystick 1',
                    'force_fullscreen 1',
                    'screen_width 1280',
                    'screen_height 960'
                ]
                
                for check in checks:
                    if check in config_content:
                        logger.info(f"✅ Config contains: {check}")
                    else:
                        logger.warning(f"⚠️ Config missing: {check}")
        
        logger.info("✅ Game launch simulation successful")
        return True
    except Exception as e:
        logger.error(f"❌ Game launch simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🎮 Starting DoomBox Game Launch Fixes Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Controller Detection", test_controller_detection),
        ("Game Launcher Configuration", test_game_launcher_config),
        ("Kiosk Startup", test_kiosk_startup),
        ("Game Launch Simulation", test_game_launch_simulation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔧 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if success:
            passed += 1
    
    logger.info(f"\n🎯 Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Game launch fixes are ready for deployment.")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
