#!/usr/bin/env python3
"""
Test script to send MQTT commands to DoomBox
"""

import paho.mqtt.client as mqtt
import json
import time
import sys

def send_command(broker_host, command_type, data):
    """Send a command via MQTT"""
    client = mqtt.Client()
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT broker at {broker_host}")
            
            # Send command
            topic = f"doombox/{command_type}"
            payload = json.dumps(data)
            client.publish(topic, payload)
            print(f"Sent command to {topic}: {payload}")
            
            # Disconnect after sending
            client.disconnect()
        else:
            print(f"Failed to connect: {rc}")
    
    client.on_connect = on_connect
    client.connect(broker_host, 1883, 60)
    client.loop_start()
    
    # Wait for message to be sent
    time.sleep(2)
    client.loop_stop()

if __name__ == "__main__":
    broker_host = "10.0.0.215"
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_mqtt_commands.py <command>")
        print("Commands:")
        print("  launch_game - Launch a game")
        print("  stop_game - Stop current game")
        print("  get_status - Get system status")
        print("  start_game - Start game via web form simulation")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "launch_game":
        send_command(broker_host, "commands", {
            "command": "launch_game",
            "player_name": "TestPlayer",
            "skill": 3
        })
    
    elif command == "stop_game":
        send_command(broker_host, "commands", {
            "command": "stop_game"
        })
    
    elif command == "get_status":
        send_command(broker_host, "commands", {
            "command": "get_status"
        })
    
    elif command == "start_game":
        send_command(broker_host, "start_game", {
            "player_name": "WebTestPlayer"
        })
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
