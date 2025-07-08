#!/usr/bin/env python3
"""
Test MQTT integration for DoomBox
"""

import sys
import os
import json
import time
import logging
from threading import Thread

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mqtt_integration():
    """Test MQTT integration with game launcher"""
    
    try:
        # Import modules with proper path handling
        import importlib.util
        
        src_dir = os.path.join(os.path.dirname(__file__), 'src')
        
        # Import mqtt-client
        mqtt_spec = importlib.util.spec_from_file_location("mqtt_client", 
                                                          os.path.join(src_dir, "mqtt-client.py"))
        mqtt_module = importlib.util.module_from_spec(mqtt_spec)
        mqtt_spec.loader.exec_module(mqtt_module)
        DoomBoxMQTTClient = mqtt_module.DoomBoxMQTTClient
        
        # Import game-launcher
        game_spec = importlib.util.spec_from_file_location("game_launcher", 
                                                          os.path.join(src_dir, "game-launcher.py"))
        game_module = importlib.util.module_from_spec(game_spec)
        game_spec.loader.exec_module(game_module)
        GameLauncher = game_module.GameLauncher
        
        print("✅ Successfully imported MQTT client and game launcher")
        
        # Initialize components
        game_launcher = GameLauncher()
        mqtt_client = DoomBoxMQTTClient()
        
        # Link them together
        mqtt_client.set_game_launcher(game_launcher)
        print("✅ Components linked successfully")
        
        # Test connection
        print("🔗 Attempting to connect to MQTT broker...")
        if mqtt_client.connect():
            print("✅ Connected to MQTT broker")
            
            # Publish test status
            mqtt_client._publish_system_status()
            print("📡 Published system status")
            
            # Wait a bit for any messages
            time.sleep(2)
            
            # Test manual game launch
            print("🎮 Testing manual game launch...")
            result = game_launcher.launch_game("TestPlayer", 3)
            if result:
                print("✅ Game launched successfully")
                time.sleep(1)
                
                # Stop game
                game_launcher.stop_game()
                print("⏹️ Game stopped")
            else:
                print("❌ Game launch failed")
                
            # Test MQTT game trigger
            print("📡 Testing MQTT game trigger...")
            test_message = {
                'command': 'launch_game',
                'player_name': 'MQTT_Test_Player',
                'skill': 3
            }
            
            # Simulate receiving an MQTT message
            mqtt_client._handle_command(test_message)
            print("✅ MQTT command handled")
            
            time.sleep(1)
            
            # Stop any running game
            game_launcher.stop_game()
            
            # Disconnect
            mqtt_client.disconnect()
            print("✅ Disconnected from MQTT broker")
            
        else:
            print("❌ Failed to connect to MQTT broker")
            print("   Make sure mosquitto is running: sudo systemctl start mosquitto")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Check that mqtt-client.py and game-launcher.py exist in src/")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    return True

def test_mqtt_message_sending():
    """Test sending MQTT messages to trigger game launches"""
    
    try:
        import paho.mqtt.client as mqtt
        import json
        
        print("\n🧪 Testing MQTT message sending...")
        
        # Create a client to send test messages
        client = mqtt.Client(client_id="test_sender")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✅ Test sender connected")
                
                # Send a game launch command
                command = {
                    'command': 'launch_game',
                    'player_name': 'MQTT_Remote_Player',
                    'skill': 4
                }
                
                client.publish('doombox/commands', json.dumps(command))
                print("📡 Sent game launch command")
                
                # Send a start game message (like from web form)
                start_message = {
                    'player_name': 'Web_Form_Player'
                }
                
                client.publish('doombox/start_game', json.dumps(start_message))
                print("📡 Sent start game message")
                
            else:
                print(f"❌ Test sender connection failed: {rc}")
        
        client.on_connect = on_connect
        
        try:
            client.connect("localhost", 1883, 60)
            client.loop_start()
            
            # Wait for messages to be sent
            time.sleep(3)
            
            client.loop_stop()
            client.disconnect()
            
        except Exception as e:
            print(f"❌ Failed to send test messages: {e}")
            return False
            
    except ImportError:
        print("❌ paho-mqtt not installed, skipping message sending test")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Testing DoomBox MQTT Integration\n")
    
    success = test_mqtt_integration()
    
    if success:
        test_mqtt_message_sending()
        print("\n✅ All tests completed!")
    else:
        print("\n❌ Basic integration test failed!")
        sys.exit(1)
