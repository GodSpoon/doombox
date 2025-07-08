#!/usr/bin/env python3
"""
Simple MQTT test for DoomBox on Radxa device
"""

import sys
import os
import json
import time
import logging
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mqtt_on_radxa():
    """Test MQTT functionality on Radxa device"""
    
    try:
        print("🔍 Testing MQTT on Radxa device...")
        
        # Get the actual script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(script_dir, 'src')
        
        print(f"📁 Script directory: {script_dir}")
        print(f"📁 Source directory: {src_dir}")
        
        # Import mqtt-client
        mqtt_path = os.path.join(src_dir, "mqtt-client.py")
        if not os.path.exists(mqtt_path):
            print(f"❌ MQTT client not found at: {mqtt_path}")
            return False
            
        mqtt_spec = importlib.util.spec_from_file_location("mqtt_client", mqtt_path)
        mqtt_module = importlib.util.module_from_spec(mqtt_spec)
        mqtt_spec.loader.exec_module(mqtt_module)
        DoomBoxMQTTClient = mqtt_module.DoomBoxMQTTClient
        
        print("✅ Successfully imported MQTT client")
        
        # Initialize MQTT client
        mqtt_client = DoomBoxMQTTClient()
        print("✅ MQTT client initialized")
        
        # Test connection
        print("🔗 Attempting to connect to MQTT broker...")
        if mqtt_client.connect():
            print("✅ Connected to MQTT broker successfully!")
            
            # Publish test status
            mqtt_client._publish_system_status()
            print("📡 Published system status")
            
            # Wait for any messages
            time.sleep(3)
            
            # Disconnect
            mqtt_client.disconnect()
            print("✅ Disconnected from MQTT broker")
            
            return True
            
        else:
            print("❌ Failed to connect to MQTT broker")
            print("   Check that:")
            print("   - Mosquitto is running on the broker")
            print("   - Network connectivity is good")
            print("   - Broker IP is correct in config")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mqtt_message_handling():
    """Test MQTT message handling without game launcher"""
    
    try:
        print("\n🧪 Testing MQTT message handling...")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(script_dir, 'src')
        
        # Import mqtt-client
        mqtt_path = os.path.join(src_dir, "mqtt-client.py")
        mqtt_spec = importlib.util.spec_from_file_location("mqtt_client", mqtt_path)
        mqtt_module = importlib.util.module_from_spec(mqtt_spec)
        mqtt_spec.loader.exec_module(mqtt_module)
        DoomBoxMQTTClient = mqtt_module.DoomBoxMQTTClient
        
        # Initialize MQTT client
        mqtt_client = DoomBoxMQTTClient()
        
        # Test command handling directly
        test_command = {
            'command': 'launch_game',
            'player_name': 'TestPlayer',
            'skill': 3
        }
        
        print("📡 Testing command handling...")
        mqtt_client._handle_command(test_command)
        print("✅ Command handling test completed")
        
        # Test start game handling
        test_start = {
            'player_name': 'WebFormPlayer'
        }
        
        print("📡 Testing start game handling...")
        mqtt_client._handle_start_game(test_start)
        print("✅ Start game handling test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during message handling test: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_test_messages():
    """Send test messages to trigger game launches"""
    
    try:
        import paho.mqtt.client as mqtt
        
        print("\n📡 Sending test MQTT messages...")
        
        # Create a client to send test messages
        client = mqtt.Client(client_id="test_sender")
        
        # Load config for broker info
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.py')
            config_spec = importlib.util.spec_from_file_location("config", config_path)
            config_module = importlib.util.module_from_spec(config_spec)
            config_spec.loader.exec_module(config_module)
            
            broker_host = config_module.MQTT_BROKER
            broker_port = config_module.MQTT_PORT
            
        except Exception as e:
            print(f"⚠️ Could not load config: {e}")
            broker_host = "localhost"
            broker_port = 1883
        
        print(f"🔗 Connecting to {broker_host}:{broker_port}")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✅ Test sender connected")
                
                # Send a game launch command
                command = {
                    'command': 'launch_game',
                    'player_name': 'MQTT_Test_Player',
                    'skill': 3
                }
                
                client.publish('doombox/commands', json.dumps(command))
                print("📡 Sent game launch command")
                
                # Send a start game message
                start_message = {
                    'player_name': 'Web_Form_Test'
                }
                
                client.publish('doombox/start_game', json.dumps(start_message))
                print("📡 Sent start game message")
                
            else:
                print(f"❌ Test sender connection failed: {rc}")
        
        client.on_connect = on_connect
        
        client.connect(broker_host, broker_port, 60)
        client.loop_start()
        
        # Wait for messages to be sent
        time.sleep(3)
        
        client.loop_stop()
        client.disconnect()
        
        print("✅ Test messages sent successfully")
        return True
        
    except ImportError:
        print("❌ paho-mqtt not installed, skipping message sending test")
        return False
    except Exception as e:
        print(f"❌ Error sending test messages: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing DoomBox MQTT Integration on Radxa\n")
    
    # Test basic MQTT functionality
    if test_mqtt_on_radxa():
        print("✅ Basic MQTT test passed")
        
        # Test message handling
        if test_mqtt_message_handling():
            print("✅ Message handling test passed")
            
            # Send test messages
            if send_test_messages():
                print("✅ Test message sending passed")
                
                print("\n🎉 All tests completed successfully!")
                print("💡 The DoomBox kiosk should now respond to MQTT game triggers")
                
            else:
                print("\n⚠️ Test message sending failed, but basic functionality works")
        else:
            print("\n❌ Message handling test failed")
            
    else:
        print("\n❌ Basic MQTT test failed")
        print("   Check MQTT broker connectivity and configuration")
        
    print("\n" + "="*50)
    print("To test manually, send MQTT messages like:")
    print("mosquitto_pub -h 10.0.0.215 -t doombox/commands -m '{\"command\":\"launch_game\",\"player_name\":\"TestPlayer\",\"skill\":3}'")
    print("mosquitto_pub -h 10.0.0.215 -t doombox/start_game -m '{\"player_name\":\"WebPlayer\"}'")
