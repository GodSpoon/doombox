#!/usr/bin/env python3
"""
Comprehensive MQTT test script for DoomBox
Tests all commands and listens for responses
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from datetime import datetime

class DoomBoxMQTTTester:
    def __init__(self, broker_host):
        self.broker_host = broker_host
        self.client = mqtt.Client()
        self.connected = False
        self.messages_received = []
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
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
                print(f"✓ Subscribed to {topic}")
        else:
            print(f"✗ Failed to connect: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("✓ Disconnected from MQTT broker")
        
    def on_message(self, client, userdata, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            print(f"[{timestamp}] 📥 {topic}: {json.dumps(payload, indent=2)}")
        except json.JSONDecodeError:
            payload = msg.payload.decode('utf-8')
            print(f"[{timestamp}] 📥 {topic}: {payload}")
        
        self.messages_received.append({
            'timestamp': timestamp,
            'topic': topic,
            'payload': payload
        })
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, 1883, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
                
            return self.connected
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
    
    def send_command(self, topic, payload):
        """Send a command"""
        if not self.connected:
            print("✗ Not connected to broker")
            return False
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
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
    
    def run_tests(self):
        """Run comprehensive MQTT tests"""
        print("\n🚀 Starting DoomBox MQTT Tests")
        print("=" * 50)
        
        if not self.connect():
            print("✗ Failed to connect to MQTT broker")
            return False
            
        # Wait a moment for subscriptions to be established
        time.sleep(2)
        
        # Test 1: Get Status
        print("\n📊 Test 1: Get Status")
        self.send_command("doombox/commands", {"command": "get_status"})
        time.sleep(3)
        
        # Test 2: Launch Game
        print("\n🎮 Test 2: Launch Game")
        self.send_command("doombox/commands", {
            "command": "launch_game",
            "player_name": "TestPlayer",
            "skill": 3
        })
        time.sleep(3)
        
        # Test 3: Stop Game
        print("\n🛑 Test 3: Stop Game")
        self.send_command("doombox/commands", {"command": "stop_game"})
        time.sleep(3)
        
        # Test 4: Start Game (Web Form)
        print("\n🌐 Test 4: Start Game (Web Form)")
        self.send_command("doombox/start_game", {"player_name": "WebTestPlayer"})
        time.sleep(3)
        
        # Test 5: Unknown Command
        print("\n❓ Test 5: Unknown Command")
        self.send_command("doombox/commands", {"command": "unknown_command"})
        time.sleep(3)
        
        # Test 6: System Commands
        print("\n⚙️ Test 6: System Commands")
        self.send_command("doombox/system", {"action": "reboot"})
        time.sleep(2)
        
        # Test 7: Player Commands
        print("\n👤 Test 7: Player Commands")
        self.send_command("doombox/players", {
            "action": "register",
            "player_name": "NewPlayer"
        })
        time.sleep(2)
        
        self.send_command("doombox/players", {
            "action": "score_update",
            "player_name": "NewPlayer",
            "score": 1000
        })
        time.sleep(2)
        
        print("\n📋 Test Summary")
        print("=" * 50)
        print(f"Total messages received: {len(self.messages_received)}")
        
        if self.messages_received:
            print("\nReceived messages:")
            for msg in self.messages_received:
                print(f"  [{msg['timestamp']}] {msg['topic']}")
        else:
            print("⚠️  No messages received - check if kiosk manager is running")
        
        self.disconnect()
        return True

def main():
    broker_host = "10.0.0.215"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--listen":
            # Just listen for messages
            tester = DoomBoxMQTTTester(broker_host)
            if tester.connect():
                print("🎧 Listening for MQTT messages... (Press Ctrl+C to stop)")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n👋 Stopping listener...")
                    tester.disconnect()
            return
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python3 test_mqtt_comprehensive.py          # Run all tests")
            print("  python3 test_mqtt_comprehensive.py --listen # Just listen for messages")
            return
    
    # Run comprehensive tests
    tester = DoomBoxMQTTTester(broker_host)
    success = tester.run_tests()
    
    if success:
        print("\n✅ MQTT tests completed")
    else:
        print("\n❌ MQTT tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
