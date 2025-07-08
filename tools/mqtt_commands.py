#!/usr/bin/env python3
"""
DoomBox MQTT Command Utility
Send commands to the DoomBox kiosk via MQTT
"""

import sys
import json
import argparse
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed. Run: pip install paho-mqtt")
    sys.exit(1)

class DoomBoxMQTTCommands:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_publish = self._on_publish
        self.connected = False
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            print(f"❌ Failed to connect to MQTT broker. Code: {rc}")
            
    def _on_publish(self, client, userdata, mid):
        print(f"📤 Message published (ID: {mid})")
        
    def connect(self):
        try:
            print(f"🔗 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            import time
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
                
            if not self.connected:
                print("❌ Connection timeout")
                return False
                
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
            
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("🔌 Disconnected from MQTT broker")
        
    def send_launch_game(self, player_name, skill=3):
        """Send launch game command"""
        command = {
            "action": "launch_game",
            "player_name": player_name,
            "skill": skill,
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/commands", json.dumps(command))
        print(f"🎮 Sent launch game command for '{player_name}' (skill: {skill})")
        return result.rc == 0
        
    def send_stop_game(self):
        """Send stop game command"""
        command = {
            "action": "stop_game",
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/commands", json.dumps(command))
        print("🛑 Sent stop game command")
        return result.rc == 0
        
    def send_status_request(self):
        """Request status from DoomBox"""
        command = {
            "action": "get_status",
            "timestamp": datetime.now().isoformat()
        }
        
        result = self.client.publish("doombox/commands", json.dumps(command))
        print("📊 Sent status request")
        return result.rc == 0

def main():
    parser = argparse.ArgumentParser(description="Send MQTT commands to DoomBox")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Launch game command
    launch_parser = subparsers.add_parser("launch", help="Launch a game")
    launch_parser.add_argument("player_name", help="Player name")
    launch_parser.add_argument("--skill", type=int, default=3, choices=[1,2,3,4,5], 
                              help="Skill level (1-5)")
    
    # Stop game command
    subparsers.add_parser("stop", help="Stop current game")
    
    # Status command
    subparsers.add_parser("status", help="Get DoomBox status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Create MQTT client
    mqtt_client = DoomBoxMQTTCommands(args.broker, args.port)
    
    if not mqtt_client.connect():
        sys.exit(1)
        
    try:
        import time
        
        if args.command == "launch":
            mqtt_client.send_launch_game(args.player_name, args.skill)
        elif args.command == "stop":
            mqtt_client.send_stop_game()
        elif args.command == "status":
            mqtt_client.send_status_request()
            
        # Give time for message to be sent
        time.sleep(1)
        
    finally:
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
