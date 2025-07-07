#!/usr/bin/env python3
"""
Simple MQTT test client to trigger game launch
"""

import paho.mqtt.client as mqtt
import json
import sys
import time
import argparse

def send_game_launch_command(broker_host="localhost", broker_port=1883, player_name="TestPlayer"):
    """Send MQTT command to launch a game"""
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {broker_host}:{broker_port}")
            
            # Send game launch command
            command = {
                "command": "launch_game",
                "player_name": player_name,
                "skill": 3
            }
            
            topic = "doombox/commands"
            payload = json.dumps(command)
            
            print(f"📤 Sending command: {payload}")
            client.publish(topic, payload)
            print(f"🎮 Game launch command sent for player: {player_name}")
            
        else:
            print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_publish(client, userdata, mid):
        print(f"✅ Message published successfully (mid: {mid})")
        # Disconnect after publishing
        client.disconnect()
    
    def on_disconnect(client, userdata, rc):
        print(f"🔌 Disconnected from MQTT broker")
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        print(f"🔌 Connecting to MQTT broker at {broker_host}:{broker_port}...")
        client.connect(broker_host, broker_port, 60)
        
        # Start loop and wait for completion
        client.loop_start()
        time.sleep(2)  # Give time for message to be sent
        client.loop_stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending MQTT command: {e}")
        return False

def send_stop_game_command(broker_host="localhost", broker_port=1883):
    """Send MQTT command to stop the current game"""
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {broker_host}:{broker_port}")
            
            # Send game stop command
            command = {
                "command": "stop_game"
            }
            
            topic = "doombox/commands"
            payload = json.dumps(command)
            
            print(f"📤 Sending command: {payload}")
            client.publish(topic, payload)
            print(f"🛑 Game stop command sent")
            
        else:
            print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_publish(client, userdata, mid):
        print(f"✅ Message published successfully (mid: {mid})")
        client.disconnect()
    
    def on_disconnect(client, userdata, rc):
        print(f"🔌 Disconnected from MQTT broker")
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        print(f"🔌 Connecting to MQTT broker at {broker_host}:{broker_port}...")
        client.connect(broker_host, broker_port, 60)
        
        # Start loop and wait for completion
        client.loop_start()
        time.sleep(2)  # Give time for message to be sent
        client.loop_stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending MQTT command: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send MQTT commands to DoomBox')
    parser.add_argument('--broker', default='localhost', help='MQTT broker hostname')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--launch', type=str, help='Launch game for player name')
    parser.add_argument('--stop', action='store_true', help='Stop current game')
    
    args = parser.parse_args()
    
    if args.launch:
        success = send_game_launch_command(args.broker, args.port, args.launch)
    elif args.stop:
        success = send_stop_game_command(args.broker, args.port)
    else:
        print("Please specify --launch <player_name> or --stop")
        print("Example: python mqtt_test_commands.py --launch TestPlayer")
        print("Example: python mqtt_test_commands.py --stop")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
