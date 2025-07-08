#!/usr/bin/env python3
"""
Test MQTT game launch functionality
Tests the complete flow from MQTT command to game launch
"""

import sys
import os
import json
import time
import threading
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ paho-mqtt not installed. Run: pip install paho-mqtt")
    sys.exit(1)

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MQTTGameLaunchTest:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.test_results = []
        self.received_responses = []
        
    def test_mqtt_connection(self):
        """Test basic MQTT connection"""
        logger.info("🔗 Testing MQTT connection...")
        
        client = mqtt.Client()
        connected = False
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected
            connected = (rc == 0)
            
        client.on_connect = on_connect
        
        try:
            client.connect(self.broker_host, self.broker_port, 60)
            client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
                
            client.loop_stop()
            client.disconnect()
            
            if connected:
                logger.info("✅ MQTT connection successful")
                return True
            else:
                logger.error("❌ MQTT connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ MQTT connection error: {e}")
            return False
            
    def test_command_sending(self):
        """Test sending commands to DoomBox"""
        logger.info("📤 Testing command sending...")
        
        client = mqtt.Client()
        published = False
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                # Send test launch command
                command = {
                    "action": "launch_game",
                    "player_name": "TestPlayer",
                    "skill": 3,
                    "timestamp": datetime.now().isoformat()
                }
                
                result = client.publish("doombox/commands", json.dumps(command))
                nonlocal published
                published = (result.rc == 0)
                logger.info(f"📨 Sent test command: {command}")
                
        client.on_connect = on_connect
        
        try:
            client.connect(self.broker_host, self.broker_port, 60)
            client.loop_start()
            
            time.sleep(2)  # Wait for message to be sent
            
            client.loop_stop()
            client.disconnect()
            
            if published:
                logger.info("✅ Command sending successful")
                return True
            else:
                logger.error("❌ Command sending failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Command sending error: {e}")
            return False
            
    def test_response_listening(self):
        """Test listening for responses from DoomBox"""
        logger.info("👂 Testing response listening...")
        
        client = mqtt.Client()
        responses_received = 0
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("doombox/status")
                client.subscribe("doombox/responses")
                logger.info("📡 Subscribed to response topics")
                
        def on_message(client, userdata, msg):
            nonlocal responses_received
            responses_received += 1
            logger.info(f"📥 Received response: {msg.topic} - {msg.payload.decode()}")
            
        client.on_connect = on_connect
        client.on_message = on_message
        
        try:
            client.connect(self.broker_host, self.broker_port, 60)
            client.loop_start()
            
            # Listen for a short time
            time.sleep(5)
            
            client.loop_stop()
            client.disconnect()
            
            logger.info(f"📊 Received {responses_received} responses")
            return True
            
        except Exception as e:
            logger.error(f"❌ Response listening error: {e}")
            return False
            
    def test_game_launcher_integration(self):
        """Test if game launcher can be imported and configured"""
        logger.info("🎮 Testing game launcher integration...")
        
        try:
            # Try to import the game launcher
            from game_launcher import GameLauncher
            
            # Test creating an instance
            launcher = GameLauncher()
            logger.info("✅ Game launcher import successful")
            
            # Test configuration
            config = launcher.get_config()
            if config:
                logger.info(f"✅ Game launcher configuration: {config}")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Game launcher import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Game launcher test error: {e}")
            return False
            
    def run_all_tests(self):
        """Run all tests and report results"""
        logger.info("🚀 Starting MQTT game launch tests...")
        logger.info("=" * 50)
        
        tests = [
            ("MQTT Connection", self.test_mqtt_connection),
            ("Command Sending", self.test_command_sending),
            ("Response Listening", self.test_response_listening),
            ("Game Launcher Integration", self.test_game_launcher_integration)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running test: {test_name}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                logger.error(f"❌ Test {test_name} failed with exception: {e}")
                results[test_name] = False
                
        # Report results
        logger.info("\n📋 Test Results Summary:")
        logger.info("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name:.<30} {status}")
            if result:
                passed += 1
                
        logger.info(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed!")
            return True
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed")
            return False

def main():
    broker_host = "localhost"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        broker_host = sys.argv[1]
        
    logger.info(f"🎯 Testing MQTT game launch with broker: {broker_host}")
    
    tester = MQTTGameLaunchTest(broker_host)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
