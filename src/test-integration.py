#!/usr/bin/env python3
"""
DoomBox Integration Test
Tests the MQTT and game launcher integration without the full kiosk
"""

import os
import sys
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mqtt_integration():
    """Test MQTT and game launcher integration"""
    try:
        # Add current directory to path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, script_dir)
        
        # Import components
        from mqtt_client import DoomBoxMQTTClient
        from game_launcher import GameLauncher
        
        logger.info("✅ Successfully imported components")
        
        # Initialize game launcher
        game_launcher = GameLauncher()
        logger.info("✅ Game launcher initialized")
        
        # Check dependencies
        if game_launcher.check_dependencies():
            logger.info("✅ Game launcher dependencies satisfied")
        else:
            logger.warning("⚠️  Game launcher dependencies missing")
        
        # Initialize MQTT client
        mqtt_client = DoomBoxMQTTClient()
        logger.info("✅ MQTT client initialized")
        
        # Connect game launcher to MQTT
        mqtt_client.set_game_launcher(game_launcher)
        logger.info("✅ Game launcher connected to MQTT client")
        
        # Test MQTT connection
        if mqtt_client.connect():
            logger.info("✅ MQTT connection successful")
            
            # Publish initial status
            mqtt_client._publish_system_status()
            logger.info("✅ Initial status published")
            
            # Wait for commands
            logger.info("🔄 Listening for MQTT commands for 30 seconds...")
            logger.info("   Send test command from host:")
            logger.info("   python3 scripts/mqtt-test-client.py --broker 10.0.0.215 launch TestPlayer")
            
            time.sleep(30)
            
            # Cleanup
            mqtt_client.disconnect()
            logger.info("✅ MQTT client disconnected")
            
        else:
            logger.error("❌ MQTT connection failed")
            return False
        
        logger.info("🎉 Integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mqtt_integration()
    sys.exit(0 if success else 1)
