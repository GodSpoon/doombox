#!/usr/bin/env python3
"""
MQTT traffic monitor for DoomBox
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
from collections import defaultdict, deque

class MQTTMonitor:
    def __init__(self, broker_host):
        self.broker_host = broker_host
        self.client = mqtt.Client()
        self.connected = False
        self.message_counts = defaultdict(int)
        self.recent_messages = deque(maxlen=10)
        self.start_time = datetime.now()
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✓ Connected to MQTT broker at {self.broker_host}")
            
            # Subscribe to all DoomBox topics
            topics = [
                "doombox/+",  # All doombox topics
                "doombox/status",
                "doombox/commands",
                "doombox/scores", 
                "doombox/players",
                "doombox/system",
                "doombox/start_game"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                
    def on_message(self, client, userdata, msg):
        timestamp = datetime.now()
        topic = msg.topic
        self.message_counts[topic] += 1
        
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Store recent message summary
            self.recent_messages.append({
                'timestamp': timestamp.strftime("%H:%M:%S.%f")[:-3],
                'topic': topic,
                'type': payload.get('type', 'data'),
                'size': len(msg.payload)
            })
            
            # Only print interesting messages (responses, not regular status)
            if topic != "doombox/status" or payload.get('type') is not None:
                print(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] {topic}: {payload.get('type', 'data')}")
                
        except json.JSONDecodeError:
            print(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] {topic}: non-JSON data")
    
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
    
    def show_stats(self):
        """Show statistics about message traffic"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n📊 MQTT Traffic Statistics ({elapsed:.1f}s)")
        print("=" * 50)
        
        total_messages = sum(self.message_counts.values())
        print(f"Total messages: {total_messages}")
        print(f"Messages per second: {total_messages/elapsed:.1f}")
        print()
        
        if self.message_counts:
            print("Messages by topic:")
            for topic, count in sorted(self.message_counts.items()):
                rate = count / elapsed
                print(f"  {topic}: {count} ({rate:.1f}/s)")
        
        print("\nRecent messages:")
        for msg in list(self.recent_messages)[-5:]:
            print(f"  [{msg['timestamp']}] {msg['topic']} - {msg['type']}")
    
    def monitor(self, duration=30):
        """Monitor MQTT traffic for specified duration"""
        print(f"🎧 Monitoring MQTT traffic for {duration} seconds...")
        print("(Only showing responses and interesting messages)")
        print("=" * 60)
        
        if not self.connect():
            print("✗ Failed to connect to MQTT broker")
            return False
            
        try:
            for i in range(duration):
                time.sleep(1)
                if (i + 1) % 10 == 0:
                    print(f"\n⏰ {i+1}s elapsed...")
                    
        except KeyboardInterrupt:
            print("\n👋 Monitoring interrupted by user")
        
        self.show_stats()
        self.disconnect()

def main():
    broker_host = "10.0.0.215"
    
    monitor = MQTTMonitor(broker_host)
    
    # Monitor for 30 seconds
    monitor.monitor(30)

if __name__ == "__main__":
    main()
