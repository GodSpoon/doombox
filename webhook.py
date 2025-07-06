#!/usr/bin/env python3
"""
Simple webhook bridge for DoomBox
Receives form submissions and triggers the kiosk

This can be deployed on a VPS or Raspberry Pi to bridge
the GitHub Pages form to your local kiosk.

Methods supported:
1. MQTT (recommended for local network)
2. File trigger (for same machine)
3. HTTP API (for remote triggering)
"""

from flask import Flask, request, jsonify
import json
import paho.mqtt.client as mqtt
import os
import logging
from datetime import datetime
import re

app = Flask(__name__)

# Configuration
MQTT_BROKER = "your-kiosk-ip"  # Replace with kiosk IP
MQTT_PORT = 1883
MQTT_TOPIC = "doombox/start_game"

# File trigger path (if webhook runs on same machine as kiosk)
TRIGGER_FILE = "/opt/doombox/new_player.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_player_name(name):
    """Sanitize player name for safety"""
    # Remove special characters, keep alphanumeric, underscore, dash
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    # Limit length
    clean_name = clean_name[:20]
    # Ensure not empty
    if not clean_name:
        clean_name = f"Player_{datetime.now().strftime('%H%M%S')}"
    return clean_name

def trigger_via_mqtt(player_name):
    """Trigger game via MQTT"""
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        message = {
            "player_name": player_name,
            "timestamp": datetime.now().isoformat()
        }
        
        client.publish(MQTT_TOPIC, json.dumps(message))
        client.disconnect()
        
        logger.info(f"MQTT trigger sent for player: {player_name}")
        return True
    except Exception as e:
        logger.error(f"MQTT trigger failed: {e}")
        return False

def trigger_via_file(player_name):
    """Trigger game via file (local machine only)"""
    try:
        data = {
            "player_name": player_name,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(TRIGGER_FILE, 'w') as f:
            json.dump(data, f)
        
        logger.info(f"File trigger created for player: {player_name}")
        return True
    except Exception as e:
        logger.error(f"File trigger failed: {e}")
        return False

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "DoomBox Webhook Bridge",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/register', methods=['POST'])
def register_player():
    """Handle player registration from web form"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'player_name' not in data:
            return jsonify({"error": "Missing player_name"}), 400
        
        player_name = sanitize_player_name(data['player_name'])
        email = data.get('email', '')
        instagram_follow = data.get('instagram_follow', False)
        agreed_terms = data.get('agreed_terms', False)
        
        # Basic validation
        if not instagram_follow:
            return jsonify({"error": "Must follow @shmegl on Instagram"}), 400
        
        if not agreed_terms:
            return jsonify({"error": "Must agree to terms"}), 400
        
        # Log registration
        logger.info(f"Player registration: {player_name} ({email})")
        
        # Store registration data (optional)
        registration_data = {
            "player_name": player_name,
            "email": email,
            "instagram_follow": instagram_follow,
            "agreed_terms": agreed_terms,
            "timestamp": datetime.now().isoformat(),
            "ip_address": request.remote_addr
        }
        
        # Save to log file
        try:
            with open("registrations.log", "a") as f:
                f.write(json.dumps(registration_data) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log registration: {e}")
        
        # Trigger game start
        success = False
        
        # Try MQTT first
        if MQTT_BROKER and MQTT_BROKER != "your-kiosk-ip":
            success = trigger_via_mqtt(player_name)
        
        # Fallback to file trigger
        if not success:
            success = trigger_via_file(player_name)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Game starting soon!",
                "player_name": player_name
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to start game. Please try again."
            }), 500
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/trigger/<player_name>', methods=['POST'])
def manual_trigger(player_name):
    """Manual game trigger endpoint (for testing)"""
    try:
        clean_name = sanitize_player_name(player_name)
        
        # Try MQTT first
        success = False
        if MQTT_BROKER and MQTT_BROKER != "your-kiosk-ip":
            success = trigger_via_mqtt(clean_name)
        
        # Fallback to file trigger
        if not success:
            success = trigger_via_file(clean_name)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Game triggered for {clean_name}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to trigger game"
            }), 500
            
    except Exception as e:
        logger.error(f"Manual trigger error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get registration statistics"""
    try:
        stats = {
            "total_registrations": 0,
            "recent_players": []
        }
        
        # Read from log file
        try:
            with open("registrations.log", "r") as f:
                lines = f.readlines()
                stats["total_registrations"] = len(lines)
                
                # Get last 10 registrations
                for line in lines[-10:]:
                    try:
                        reg_data = json.loads(line.strip())
                        stats["recent_players"].append({
                            "player_name": reg_data["player_name"],
                            "timestamp": reg_data["timestamp"]
                        })
                    except:
                        continue
        except FileNotFoundError:
            pass
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🎮 DoomBox Webhook Bridge Starting...")
    print(f"📡 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"📁 Trigger File: {TRIGGER_FILE}")
    print("🌐 Webhook URL: http://your-server:5000/register")
    print("\nEndpoints:")
    print("  GET  /          - Health check")
    print("  POST /register  - Player registration")
    print("  POST /trigger/<name> - Manual trigger")
    print("  GET  /stats     - Registration stats")
    print("\nStarting server...")
    
    # Run with debug=False in production
    app.run(host='0.0.0.0', port=5000, debug=True)
