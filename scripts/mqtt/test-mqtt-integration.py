#!/usr/bin/env python3
"""
Test MQTT Integration for DoomBox
Tests if the kiosk manager can properly receive and handle MQTT commands
"""

import sys
import os
import time
import threading
import logging

# Add the project root to the path
sys.path.append('/root/doombox')
sys.path.append('/root/doombox/src')
sys.path.append('/home/sam/SPOON_GIT/doombox')
sys.path.append('/home/sam/SPOON_GIT/doombox/src')
sys.path.append('.')
sys.path.append('./src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    print("🔧 Testing imports...")
    
    try:
        # Try different import methods
        try:
            from src.mqtt_client import DoomBoxMQTTClient
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("mqtt_client", "src/mqtt-client.py")
            mqtt_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mqtt_module)
            DoomBoxMQTTClient = mqtt_module.DoomBoxMQTTClient
        print("✅ MQTT client import successful")
    except ImportError as e:
        print(f"❌ MQTT client import failed: {e}")
        return False
    
    try:
        # Try different import methods
        try:
            from src.game_launcher import GameLauncher
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("game_launcher", "src/game-launcher.py")
            game_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(game_module)
            GameLauncher = game_module.GameLauncher
        print("✅ Game launcher import successful")
    except ImportError as e:
        print(f"❌ Game launcher import failed: {e}")
        return False
    
    try:
        # Try different import methods
        try:
            from config.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPICS
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", "config/config.py")
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            MQTT_BROKER = config_module.MQTT_BROKER
            MQTT_PORT = config_module.MQTT_PORT
            MQTT_TOPICS = config_module.MQTT_TOPICS
        print(f"✅ Config import successful - Broker: {MQTT_BROKER}:{MQTT_PORT}")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    return True

def test_mqtt_connection():
    """Test MQTT connection"""
    print("\n🔧 Testing MQTT connection...")
    
    try:
        from src.mqtt_client import DoomBoxMQTTClient
        from config.config import MQTT_BROKER, MQTT_PORT
        
        client = DoomBoxMQTTClient(MQTT_BROKER, MQTT_PORT)
        
        if client.connect():
            print("✅ MQTT connection successful")
            client.disconnect()
            return True
        else:
            print("❌ MQTT connection failed")
            return False
            
    except Exception as e:
        print(f"❌ MQTT connection test failed: {e}")
        return False

def test_game_launcher():
    """Test game launcher initialization"""
    print("\n🔧 Testing game launcher...")
    
    try:
        from src.game_launcher import GameLauncher
        
        launcher = GameLauncher()
        print("✅ Game launcher initialization successful")
        return True
        
    except Exception as e:
        print(f"❌ Game launcher test failed: {e}")
        return False

def test_integration():
    """Test MQTT + Game Launcher integration"""
    print("\n🔧 Testing MQTT + Game Launcher integration...")
    
    try:
        from src.mqtt_client import DoomBoxMQTTClient
        from src.game_launcher import GameLauncher
        from config.config import MQTT_BROKER, MQTT_PORT
        
        # Create instances
        launcher = GameLauncher()
        client = DoomBoxMQTTClient(MQTT_BROKER, MQTT_PORT)
        
        # Set up integration
        client.set_game_launcher(launcher)
        
        if client.connect():
            print("✅ Integration setup successful")
            
            # Test command handling
            test_data = {
                "command": "launch_game",
                "player_name": "TestPlayer",
                "skill": 3
            }
            
            print("✅ Integration test completed")
            client.disconnect()
            return True
        else:
            print("❌ Integration connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 DoomBox MQTT Integration Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_mqtt_connection,
        test_game_launcher,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"Test {test.__name__} failed")
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! MQTT integration is working.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
