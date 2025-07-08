#!/usr/bin/env python3
"""
Comprehensive MQTT Game Launch Test
Tests the complete flow from MQTT command to game launch
"""

import sys
import os
import json
import time
import logging
import threading
import subprocess
import signal
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mqtt_imports():
    """Test that all required modules can be imported"""
    try:
        import paho.mqtt.client as mqtt
        logger.info("✅ paho-mqtt imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import paho-mqtt: {e}")
        return False

def test_game_launcher_standalone():
    """Test game launcher without MQTT"""
    try:
        from game_launcher import GameLauncher
        
        launcher = GameLauncher()
        logger.info("✅ GameLauncher created successfully")
        
        # Test configuration
        if launcher.setup_doom_config():
            logger.info("✅ Doom config setup successful")
        else:
            logger.warning("⚠️ Doom config setup failed")
        
        # Test executable detection
        if launcher.doom_config.get('executable'):
            logger.info(f"✅ Doom executable found: {launcher.doom_config['executable']}")
        else:
            logger.warning("⚠️ Doom executable not found")
        
        # Test controller detection
        controllers = launcher.check_controllers()
        logger.info(f"🎮 Controllers found: {controllers['controllers_found']}")
        logger.info(f"🕹️ Joystick devices: {controllers['joysticks_found']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GameLauncher test failed: {e}")
        return False

def test_mqtt_client_standalone():
    """Test MQTT client without game launcher"""
    try:
        from mqtt_client import DoomBoxMQTTClient
        
        client = DoomBoxMQTTClient()
        logger.info("✅ DoomBoxMQTTClient created successfully")
        
        # Test configuration
        logger.info(f"🌐 MQTT Broker: {client.broker_host}:{client.broker_port}")
        logger.info(f"📡 Topics: {list(client.topics.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MQTT client test failed: {e}")
        return False

def test_mqtt_connection():
    """Test MQTT broker connection"""
    try:
        import paho.mqtt.client as mqtt
        
        connected = False
        connection_result = None
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected, connection_result
            connected = True
            connection_result = rc
            logger.info(f"MQTT Connection result: {rc}")
            client.disconnect()
        
        client = mqtt.Client()
        client.on_connect = on_connect
        
        # Try to connect to the broker
        from config.config import MQTT_BROKER, MQTT_PORT
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 10
        while not connected and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        
        client.loop_stop()
        
        if connected and connection_result == 0:
            logger.info("✅ MQTT broker connection successful")
            return True
        else:
            logger.error(f"❌ MQTT broker connection failed: {connection_result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ MQTT connection test failed: {e}")
        return False

def test_integrated_mqtt_game_launch():
    """Test full integration: MQTT client + Game launcher"""
    try:
        from mqtt_client import DoomBoxMQTTClient
        from game_launcher import GameLauncher
        
        # Create components
        game_launcher = GameLauncher()
        mqtt_client = DoomBoxMQTTClient()
        
        # Link them together
        mqtt_client.set_game_launcher(game_launcher)
        
        # Test connection
        if mqtt_client.connect():
            logger.info("✅ MQTT client connected for integration test")
            
            # Publish initial status
            mqtt_client._publish_system_status()
            logger.info("📡 Published initial system status")
            
            # Keep running for a short time to receive messages
            logger.info("🔄 Listening for MQTT messages for 5 seconds...")
            time.sleep(5)
            
            mqtt_client.disconnect()
            logger.info("✅ Integration test completed successfully")
            return True
        else:
            logger.error("❌ MQTT connection failed for integration test")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def send_test_game_command():
    """Send a test game launch command via MQTT"""
    try:
        import paho.mqtt.client as mqtt
        from config.config import MQTT_BROKER, MQTT_PORT
        
        command_sent = False
        
        def on_connect(client, userdata, flags, rc):
            nonlocal command_sent
            if rc == 0:
                logger.info("✅ Test command sender connected")
                
                # Send game launch command
                command = {
                    'command': 'launch_game',
                    'player_name': 'MQTT_Test_Player',
                    'skill': 3,
                    'timestamp': datetime.now().isoformat()
                }
                
                payload = json.dumps(command)
                client.publish('doombox/commands', payload)
                logger.info(f"📤 Sent game launch command: {payload}")
                command_sent = True
                
                # Send status request
                status_command = {
                    'command': 'get_status',
                    'timestamp': datetime.now().isoformat()
                }
                
                status_payload = json.dumps(status_command)
                client.publish('doombox/commands', status_payload)
                logger.info(f"📤 Sent status request: {status_payload}")
                
                # Send web form simulation
                web_form_data = {
                    'player_name': 'Web_Form_Test',
                    'timestamp': datetime.now().isoformat()
                }
                
                web_payload = json.dumps(web_form_data)
                client.publish('doombox/start_game', web_payload)
                logger.info(f"📤 Sent web form simulation: {web_payload}")
                
                client.disconnect()
            else:
                logger.error(f"❌ Test command sender connection failed: {rc}")
        
        client = mqtt.Client()
        client.on_connect = on_connect
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Wait for command to be sent
        timeout = 5
        while not command_sent and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        
        client.loop_stop()
        
        if command_sent:
            logger.info("✅ Test commands sent successfully")
            return True
        else:
            logger.error("❌ Failed to send test commands")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test command sending failed: {e}")
        return False

def monitor_mqtt_responses():
    """Monitor MQTT responses from the kiosk"""
    try:
        import paho.mqtt.client as mqtt
        from config.config import MQTT_BROKER, MQTT_PORT
        
        responses_received = 0
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✅ Response monitor connected")
                # Subscribe to all doombox topics
                client.subscribe('doombox/+')
                logger.info("📡 Subscribed to all doombox topics")
            else:
                logger.error(f"❌ Response monitor connection failed: {rc}")
        
        def on_message(client, userdata, msg):
            nonlocal responses_received
            try:
                topic = msg.topic
                payload = msg.payload.decode('utf-8')
                logger.info(f"📨 Received on {topic}: {payload}")
                responses_received += 1
                
                # Try to parse as JSON for better display
                try:
                    data = json.loads(payload)
                    logger.info(f"   📋 Parsed data: {data}")
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Monitor for 10 seconds
        logger.info("🔄 Monitoring MQTT responses for 10 seconds...")
        time.sleep(10)
        
        client.loop_stop()
        client.disconnect()
        
        logger.info(f"✅ Monitoring completed. Received {responses_received} responses")
        return responses_received > 0
        
    except Exception as e:
        logger.error(f"❌ MQTT monitoring failed: {e}")
        return False

def test_game_launch_direct():
    """Test game launch directly without MQTT"""
    try:
        from game_launcher import GameLauncher
        
        launcher = GameLauncher()
        
        # Test launch (this should start the game if everything is configured)
        logger.info("🎮 Testing direct game launch...")
        
        # Launch game for a test player
        success = launcher.launch_game("Direct_Test_Player", skill=3)
        
        if success:
            logger.info("✅ Game launch initiated successfully")
            
            # Check if game is running
            time.sleep(2)
            if launcher.is_game_running():
                logger.info("✅ Game is running")
                
                # Stop the game after a short time
                logger.info("🛑 Stopping game after 3 seconds...")
                time.sleep(3)
                launcher.stop_game()
                logger.info("✅ Game stopped")
                
                return True
            else:
                logger.warning("⚠️ Game launch succeeded but game is not running")
                return False
        else:
            logger.error("❌ Game launch failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Direct game launch test failed: {e}")
        return False

def main():
    """Run comprehensive MQTT game launch tests"""
    print("🔍 DoomBox MQTT Game Launch Comprehensive Test")
    print("=" * 50)
    
    tests = [
        ("MQTT Imports", test_mqtt_imports),
        ("Game Launcher Standalone", test_game_launcher_standalone),
        ("MQTT Client Standalone", test_mqtt_client_standalone),
        ("MQTT Broker Connection", test_mqtt_connection),
        ("Direct Game Launch", test_game_launch_direct),
        ("Integrated MQTT+Game", test_integrated_mqtt_game_launch),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Now testing live MQTT commands...")
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_mqtt_responses, daemon=True)
        monitor_thread.start()
        
        # Wait a moment for monitor to start
        time.sleep(2)
        
        # Send test commands
        if send_test_game_command():
            print("✅ Test commands sent successfully")
        else:
            print("❌ Failed to send test commands")
        
        # Wait for monitor to complete
        monitor_thread.join(timeout=12)
        
        print("\n🚀 MQTT Game Launch Testing Complete!")
        print("If you see game launch responses, the system is working correctly.")
        
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the logs and fix issues.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
