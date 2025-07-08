#!/usr/bin/env python3
"""
DoomBox MQTT Test Client
Sends test commands to the DoomBox kiosk via MQTT
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import argparse
from datetime import datetime

class DoomBoxTestClient:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(client_id=f"doombox_test_{int(time.time())}")
        self.connected = False
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Subscribe to response topics
        self.client.message_callback_add("doombox/status", self._on_status_message)
        
    def _on_connect(self, client, userdata, flags, rc):
        """Called when client connects to broker"""
        if rc == 0:
            self.connected = True
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all doombox topics for monitoring
            client.subscribe("doombox/#")
            print("📡 Subscribed to all doombox topics")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Called when client disconnects from broker"""
        self.connected = False
        print("📡 Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Called when any message is received"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        print(f"📨 [{topic}] {payload}")
    
    def _on_status_message(self, client, userdata, msg):
        """Handle status messages specifically"""
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            print(f"📊 Status Update: {json.dumps(data, indent=2)}")
        except:
            print(f"📊 Status: {msg.payload.decode('utf-8')}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            return self.connected
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
    
    def send_launch_game(self, player_name, skill=3):
        """Send launch game command"""
        if not self.connected:
            print("❌ Not connected to broker")
            return False
        
        message = {
            "command": "launch_game",
            "player_name": player_name,
            "skill": skill,
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/commands", json.dumps(message))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"🎮 Game launch command sent for player: {player_name}")
            return True
        else:
            print(f"❌ Failed to send command: {result.rc}")
            return False
    
    def send_stop_game(self):
        """Send stop game command"""
        if not self.connected:
            print("❌ Not connected to broker")
            return False
        
        message = {
            "command": "stop_game",
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/commands", json.dumps(message))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("🛑 Game stop command sent")
            return True
        else:
            print(f"❌ Failed to send command: {result.rc}")
            return False
    
    def send_get_status(self):
        """Send get status command"""
        if not self.connected:
            print("❌ Not connected to broker")
            return False
        
        message = {
            "command": "get_status",
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/commands", json.dumps(message))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("📊 Status request sent")
            return True
        else:
            print(f"❌ Failed to send command: {result.rc}")
            return False
    
    def send_player_registration(self, player_name):
        """Send player registration (like from web form)"""
        if not self.connected:
            print("❌ Not connected to broker")
            return False
        
        message = {
            "player_name": player_name,
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/start_game", json.dumps(message))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📝 Player registration sent: {player_name}")
            return True
        else:
            print(f"❌ Failed to send registration: {result.rc}")
            return False
    
    def monitor_mode(self, duration=30):
        """Monitor all doombox messages for a given duration"""
        print(f"👁️  Monitoring doombox messages for {duration} seconds...")
        print("   Press Ctrl+C to stop early")
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\n👁️  Monitoring stopped by user")

def main():
    parser = argparse.ArgumentParser(description='DoomBox MQTT Test Client')
    parser.add_argument('--broker', default='localhost', help='MQTT broker hostname')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--player', default='TestPlayer', help='Player name for game launch')
    parser.add_argument('--skill', type=int, default=3, help='Doom skill level (1-5)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Launch game command
    launch_parser = subparsers.add_parser('launch', help='Launch game for player')
    launch_parser.add_argument('player_name', help='Player name')
    launch_parser.add_argument('--skill', type=int, default=3, help='Skill level (1-5)')
    
    # Stop game command
    subparsers.add_parser('stop', help='Stop current game')
    
    # Status command
    subparsers.add_parser('status', help='Get kiosk status')
    
    # Register player command (simulates web form)
    register_parser = subparsers.add_parser('register', help='Register player (simulates web form)')
    register_parser.add_argument('player_name', help='Player name')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor all doombox messages')
    monitor_parser.add_argument('--duration', type=int, default=30, help='Monitor duration in seconds')
    
    # Interactive mode
    subparsers.add_parser('interactive', help='Interactive test mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create test client
    client = DoomBoxTestClient(args.broker, args.port)
    
    try:
        if not client.connect():
            print("❌ Failed to connect to MQTT broker")
            return 1
        
        if args.command == 'launch':
            client.send_launch_game(args.player_name, args.skill)
            time.sleep(2)  # Wait for response
            
        elif args.command == 'stop':
            client.send_stop_game()
            time.sleep(2)
            
        elif args.command == 'status':
            client.send_get_status()
            time.sleep(2)
            
        elif args.command == 'register':
            client.send_player_registration(args.player_name)
            time.sleep(2)
            
        elif args.command == 'monitor':
            client.monitor_mode(args.duration)
            
        elif args.command == 'interactive':
            interactive_mode(client)
    
    except KeyboardInterrupt:
        print("\n🛑 Test client interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        client.disconnect()
    
    return 0

def interactive_mode(client):
    """Interactive test mode"""
    print("\n🎮 DoomBox Interactive Test Mode")
    print("Commands:")
    print("  1. Launch game for player")
    print("  2. Stop current game")
    print("  3. Get status")
    print("  4. Register player (web form simulation)")
    print("  5. Monitor messages")
    print("  q. Quit")
    
    while True:
        try:
            choice = input("\nEnter command (1-5, q): ").strip()
            
            if choice == 'q':
                break
            elif choice == '1':
                player_name = input("Enter player name: ").strip()
                skill = input("Enter skill level (1-5, default 3): ").strip()
                skill = int(skill) if skill else 3
                client.send_launch_game(player_name, skill)
                
            elif choice == '2':
                client.send_stop_game()
                
            elif choice == '3':
                client.send_get_status()
                
            elif choice == '4':
                player_name = input("Enter player name: ").strip()
                client.send_player_registration(player_name)
                
            elif choice == '5':
                duration = input("Monitor duration (seconds, default 30): ").strip()
                duration = int(duration) if duration else 30
                client.monitor_mode(duration)
                
            else:
                print("Invalid choice")
                
            time.sleep(1)  # Brief pause for responses
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    sys.exit(main())
