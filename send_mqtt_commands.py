#!/usr/bin/env python3
"""
MQTT Game Launch Command Sender (for Arch Host)
Sends game launch commands to the Radxa kiosk via MQTT
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import argparse
from datetime import datetime

def send_game_launch_command(broker_host, player_name, skill=3):
    """Send MQTT game launch command to the kiosk"""
    
    connected = False
    command_sent = False
    
    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        if rc == 0:
            connected = True
            print(f"✅ Connected to MQTT broker at {broker_host}")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def on_publish(client, userdata, mid):
        nonlocal command_sent
        command_sent = True
        print("📤 Game launch command sent successfully")
    
    def on_message(client, userdata, msg):
        """Handle responses from the kiosk"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            print(f"📨 Response from kiosk on {topic}:")
            
            try:
                data = json.loads(payload)
                print(f"   📋 Data: {json.dumps(data, indent=2)}")
            except:
                print(f"   📋 Raw: {payload}")
        except Exception as e:
            print(f"❌ Error processing response: {e}")
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    
    try:
        # Connect to broker
        client.connect(broker_host, 1883, 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 5
        while not connected and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        
        if not connected:
            print("❌ Failed to connect to MQTT broker")
            return False
        
        # Subscribe to responses
        client.subscribe('doombox/status')
        client.subscribe('doombox/+')  # Subscribe to all doombox topics
        print("📡 Subscribed to doombox response topics")
        
        # Create game launch command
        command = {
            'command': 'launch_game',
            'player_name': player_name,
            'skill': skill,
            'timestamp': datetime.now().isoformat()
        }
        
        payload = json.dumps(command)
        print(f"🎮 Sending game launch command for player: {player_name}")
        print(f"   Command: {payload}")
        
        # Send command
        client.publish('doombox/commands', payload)
        
        # Wait for command to be sent and listen for responses
        print("🔄 Waiting for responses (10 seconds)...")
        time.sleep(10)
        
        client.loop_stop()
        client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending command: {e}")
        return False

def send_status_request(broker_host):
    """Send status request to the kiosk"""
    
    connected = False
    
    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        if rc == 0:
            connected = True
            print(f"✅ Connected to MQTT broker at {broker_host}")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def on_message(client, userdata, msg):
        """Handle responses from the kiosk"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            print(f"📨 Kiosk status on {topic}:")
            
            try:
                data = json.loads(payload)
                print(f"   📋 Data: {json.dumps(data, indent=2)}")
            except:
                print(f"   📋 Raw: {payload}")
        except Exception as e:
            print(f"❌ Error processing response: {e}")
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect to broker
        client.connect(broker_host, 1883, 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 5
        while not connected and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        
        if not connected:
            print("❌ Failed to connect to MQTT broker")
            return False
        
        # Subscribe to responses
        client.subscribe('doombox/+')
        print("📡 Subscribed to all doombox topics")
        
        # Send status request
        status_command = {
            'command': 'get_status',
            'timestamp': datetime.now().isoformat()
        }
        
        payload = json.dumps(status_command)
        print(f"📋 Sending status request: {payload}")
        
        client.publish('doombox/commands', payload)
        
        # Wait for responses
        print("🔄 Waiting for status response (5 seconds)...")
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending status request: {e}")
        return False

def monitor_kiosk(broker_host, duration=30):
    """Monitor all messages from the kiosk"""
    
    connected = False
    message_count = 0
    
    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        if rc == 0:
            connected = True
            print(f"✅ Connected to MQTT broker at {broker_host}")
            print(f"🔄 Monitoring kiosk messages for {duration} seconds...")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def on_message(client, userdata, msg):
        """Handle all messages from the kiosk"""
        nonlocal message_count
        message_count += 1
        
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] 📨 {topic}:")
            
            try:
                data = json.loads(payload)
                print(f"   📋 {json.dumps(data, indent=2)}")
            except:
                print(f"   📋 {payload}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect to broker
        client.connect(broker_host, 1883, 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 5
        while not connected and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        
        if not connected:
            print("❌ Failed to connect to MQTT broker")
            return False
        
        # Subscribe to all doombox topics
        client.subscribe('doombox/+')
        print("📡 Subscribed to all doombox topics")
        
        # Monitor for specified duration
        time.sleep(duration)
        
        client.loop_stop()
        client.disconnect()
        
        print(f"✅ Monitoring completed. Received {message_count} messages")
        return True
        
    except Exception as e:
        print(f"❌ Error monitoring kiosk: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send MQTT commands to DoomBox kiosk')
    parser.add_argument('--broker', default='10.0.0.215', help='MQTT broker IP address')
    parser.add_argument('--radxa', default='10.0.0.234', help='Radxa kiosk IP address (for reference)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Launch game command
    launch_parser = subparsers.add_parser('launch', help='Launch game for player')
    launch_parser.add_argument('player_name', help='Player name')
    launch_parser.add_argument('--skill', type=int, default=3, help='Skill level (1-5)')
    
    # Status command
    subparsers.add_parser('status', help='Get kiosk status')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor kiosk messages')
    monitor_parser.add_argument('--duration', type=int, default=30, help='Monitor duration in seconds')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\nExamples:")
        print("  python3 send_mqtt_commands.py launch TestPlayer")
        print("  python3 send_mqtt_commands.py launch TestPlayer --skill 4")
        print("  python3 send_mqtt_commands.py status")
        print("  python3 send_mqtt_commands.py monitor --duration 60")
        return 1
    
    print(f"🌐 MQTT Broker: {args.broker}")
    print(f"📱 Radxa Kiosk: {args.radxa}")
    print("-" * 50)
    
    if args.command == 'launch':
        return 0 if send_game_launch_command(args.broker, args.player_name, args.skill) else 1
    elif args.command == 'status':
        return 0 if send_status_request(args.broker) else 1
    elif args.command == 'monitor':
        return 0 if monitor_kiosk(args.broker, args.duration) else 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
