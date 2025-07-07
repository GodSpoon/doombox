#!/usr/bin/env python3
"""
Focused MQTT test for investigating stop_game and start_game responses
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from datetime import datetime

class FocusedMQTTTester:
    def __init__(self, broker_host):
        self.broker_host = broker_host
        self.client = mqtt.Client()
        self.connected = False
        self.responses = []
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✓ Connected to MQTT broker at {self.broker_host}")
            
            # Subscribe to all DoomBox topics
            topics = [
                "doombox/status",
                "doombox/scores", 
                "doombox/players",
                "doombox/system"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                
    def on_message(self, client, userdata, msg):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Filter out frequent status updates that don't contain responses
            if topic == "doombox/status" and payload.get("type") is None:
                return  # Skip regular status updates
                
            print(f"[{timestamp}] 📥 {topic}: {json.dumps(payload, indent=2)}")
            self.responses.append({
                'timestamp': timestamp,
                'topic': topic,
                'payload': payload
            })
        except json.JSONDecodeError:
            payload = msg.payload.decode('utf-8')
            print(f"[{timestamp}] 📥 {topic}: {payload}")
        
    def connect(self):
        try:
            self.client.connect(self.broker_host, 1883, 60)
            self.client.loop_start()
            
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
                
            return self.connected
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
    
    def send_command(self, topic, payload):
        if not self.connected:
            print("✗ Not connected to broker")
            return False
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            payload_str = json.dumps(payload)
            result = self.client.publish(topic, payload_str)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[{timestamp}] 📤 {topic}: {payload_str}")
                return True
            else:
                print(f"✗ Failed to send command: {result.rc}")
                return False
        except Exception as e:
            print(f"✗ Error sending command: {e}")
            return False
    
    def test_stop_game_response(self):
        """Test stop_game command and wait for response"""
        print("\n🛑 Testing stop_game command response...")
        print("=" * 50)
        
        if not self.connect():
            print("✗ Failed to connect to MQTT broker")
            return False
            
        # Clear previous responses
        self.responses = []
        
        # Send stop_game command
        self.send_command("doombox/commands", {"command": "stop_game"})
        
        # Wait for response
        print("Waiting for response...")
        time.sleep(5)
        
        # Check responses
        if self.responses:
            print(f"\n✓ Received {len(self.responses)} response(s):")
            for resp in self.responses:
                print(f"  [{resp['timestamp']}] {resp['topic']}")
        else:
            print("⚠️  No responses received")
            
        self.disconnect()
        
    def test_start_game_response(self):
        """Test start_game command and wait for response"""
        print("\n🌐 Testing start_game (web form) command response...")
        print("=" * 50)
        
        if not self.connect():
            print("✗ Failed to connect to MQTT broker")
            return False
            
        # Clear previous responses
        self.responses = []
        
        # Send start_game command
        self.send_command("doombox/start_game", {"player_name": "WebTestPlayer"})
        
        # Wait for response
        print("Waiting for response...")
        time.sleep(5)
        
        # Check responses
        if self.responses:
            print(f"\n✓ Received {len(self.responses)} response(s):")
            for resp in self.responses:
                print(f"  [{resp['timestamp']}] {resp['topic']}")
        else:
            print("⚠️  No responses received")
            
        self.disconnect()
        
    def test_sequential_commands(self):
        """Test launch -> stop -> start sequence"""
        print("\n🔄 Testing sequential commands: launch -> stop -> start...")
        print("=" * 60)
        
        if not self.connect():
            print("✗ Failed to connect to MQTT broker")
            return False
            
        # Clear previous responses
        self.responses = []
        
        # Test sequence
        print("\n1. Launching game...")
        self.send_command("doombox/commands", {
            "command": "launch_game",
            "player_name": "SeqTestPlayer",
            "skill": 2
        })
        time.sleep(3)
        
        print("\n2. Stopping game...")
        self.send_command("doombox/commands", {"command": "stop_game"})
        time.sleep(3)
        
        print("\n3. Starting game via web form...")
        self.send_command("doombox/start_game", {"player_name": "WebSeqPlayer"})
        time.sleep(3)
        
        print("\n4. Getting final status...")
        self.send_command("doombox/commands", {"command": "get_status"})
        time.sleep(2)
        
        # Summary
        print(f"\n📋 Total responses received: {len(self.responses)}")
        if self.responses:
            print("Response summary:")
            for resp in self.responses:
                resp_type = resp['payload'].get('type', 'status_update')
                print(f"  [{resp['timestamp']}] {resp['topic']} - {resp_type}")
        
        self.disconnect()

def main():
    broker_host = "10.0.0.215"
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    tester = FocusedMQTTTester(broker_host)
    
    if test_type == "stop" or test_type == "all":
        tester.test_stop_game_response()
        time.sleep(2)
        
    if test_type == "start" or test_type == "all":
        tester.test_start_game_response()
        time.sleep(2)
        
    if test_type == "sequence" or test_type == "all":
        tester.test_sequential_commands()

if __name__ == "__main__":
    main()
