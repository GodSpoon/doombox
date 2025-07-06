#!/usr/bin/env python3
"""
DoomBox MQTT Integration (Skeleton)
Handles MQTT communication for remote game control
Ready for server integration
"""

import paho.mqtt.client as mqtt
import json
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DoomBoxMQTTClient:
    """MQTT client for DoomBox remote control"""
    
    def __init__(self, broker_host: str = None, broker_port: int = None):
        # Try to import configuration
        try:
            from config.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPICS
            self.broker_host = broker_host or MQTT_BROKER
            self.broker_port = broker_port or MQTT_PORT
            self.topics = MQTT_TOPICS
        except ImportError:
            # Fallback configuration
            self.broker_host = broker_host or "localhost"
            self.broker_port = broker_port or 1883
            self.topics = {
                'commands': 'doombox/commands',
                'status': 'doombox/status',
                'scores': 'doombox/scores',
                'players': 'doombox/players',
                'system': 'doombox/system',
                'start_game': 'doombox/start_game'
            }
        
        self.client_id = f"doombox_{int(time.time())}"
        
        # MQTT client
        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False
        
        # Callbacks
        self.message_callbacks: Dict[str, Callable] = {}
        
        # Setup MQTT client
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Game launcher reference (to be set externally)
        self.game_launcher = None
        
        logger.info(f"MQTT client initialized: {self.client_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Called when MQTT client connects"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to command topics
            for topic in self.topics.values():
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Called when MQTT client disconnects"""
        self.connected = False
        logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Called when a message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Received message on {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON payload: {payload}")
                return
            
            # Route message to appropriate handler
            if topic == self.topics['commands']:
                self._handle_command(data)
            elif topic == self.topics['start_game']:
                self._handle_start_game(data)
            elif topic == self.topics['status']:
                self._handle_status_request(data)
            elif topic == self.topics['players']:
                self._handle_player_message(data)
            elif topic == self.topics['system']:
                self._handle_system_message(data)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_command(self, data: Dict[str, Any]):
        """Handle command messages"""
        command = data.get('command')
        
        if command == 'launch_game':
            player_name = data.get('player_name', 'Unknown')
            skill = data.get('skill', 3)
            
            logger.info(f"Launching game for {player_name} (skill: {skill})")
            
            if self.game_launcher:
                success = self.game_launcher.launch_game(player_name, skill)
                self._publish_response('game_launch_response', {
                    'success': success,
                    'player_name': player_name,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.error("Game launcher not available")
        
        elif command == 'stop_game':
            logger.info("Stopping current game")
            
            if self.game_launcher:
                success = self.game_launcher.stop_game()
                self._publish_response('game_stop_response', {
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.error("Game launcher not available")
        
        elif command == 'get_status':
            self._publish_system_status()
        
        else:
            logger.warning(f"Unknown command: {command}")
    
    def _handle_start_game(self, data: Dict[str, Any]):
        """Handle start game messages from web form"""
        player_name = data.get('player_name', 'Unknown')
        skill = 3  # Default skill level
        
        logger.info(f"Start game request from web form: {player_name}")
        
        if self.game_launcher:
            success = self.game_launcher.launch_game(player_name, skill)
            self._publish_response('game_launch_response', {
                'success': success,
                'player_name': player_name,
                'source': 'web_form',
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.error("Game launcher not available")
    
    def _handle_status_request(self, data: Dict[str, Any]):
        """Handle status request messages"""
        self._publish_system_status()
    
    def _handle_player_message(self, data: Dict[str, Any]):
        """Handle player-related messages"""
        action = data.get('action')
        
        if action == 'register':
            player_name = data.get('player_name')
            logger.info(f"Player registered: {player_name}")
            # Handle player registration
        
        elif action == 'score_update':
            player_name = data.get('player_name')
            score = data.get('score')
            logger.info(f"Score update: {player_name} = {score}")
            # Handle score update
    
    def _handle_system_message(self, data: Dict[str, Any]):
        """Handle system messages"""
        action = data.get('action')
        
        if action == 'reboot':
            logger.info("System reboot requested")
            # Handle system reboot
        
        elif action == 'shutdown':
            logger.info("System shutdown requested")
            # Handle system shutdown
    
    def _publish_response(self, response_type: str, data: Dict[str, Any]):
        """Publish response message"""
        message = {
            'type': response_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.publish(self.topics['status'], json.dumps(message))
    
    def _publish_system_status(self):
        """Publish current system status"""
        status = {
            'connected': self.connected,
            'client_id': self.client_id,
            'game_running': self.game_launcher.is_game_running() if self.game_launcher else False,
            'current_player': self.game_launcher.current_player if self.game_launcher else None,
            'timestamp': datetime.now().isoformat()
        }
        
        self.publish(self.topics['status'], json.dumps(status))
    
    def connect(self) -> bool:
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
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
    
    def publish(self, topic: str, payload: str) -> bool:
        """Publish message to topic"""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            result = self.client.publish(topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def set_game_launcher(self, game_launcher):
        """Set game launcher reference"""
        self.game_launcher = game_launcher
        logger.info("Game launcher reference set")
    
    def publish_score(self, player_name: str, score: int):
        """Publish score update"""
        message = {
            'player_name': player_name,
            'score': score,
            'timestamp': datetime.now().isoformat()
        }
        
        self.publish(self.topics['scores'], json.dumps(message))
    
    def publish_player_registered(self, player_name: str):
        """Publish player registration"""
        message = {
            'action': 'registered',
            'player_name': player_name,
            'timestamp': datetime.now().isoformat()
        }
        
        self.publish(self.topics['players'], json.dumps(message))

def main():
    """Test MQTT client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DoomBox MQTT Client')
    parser.add_argument('--broker', default='localhost', help='MQTT broker hostname')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    
    args = parser.parse_args()
    
    # Create MQTT client
    mqtt_client = DoomBoxMQTTClient(args.broker, args.port)
    
    try:
        if args.test:
            print("Testing MQTT client...")
            
            if mqtt_client.connect():
                print("✓ Connected to MQTT broker")
                
                # Publish test message
                test_message = {
                    'message': 'DoomBox MQTT client test',
                    'timestamp': datetime.now().isoformat()
                }
                
                if mqtt_client.publish('doombox/test', json.dumps(test_message)):
                    print("✓ Published test message")
                else:
                    print("✗ Failed to publish test message")
                
                # Wait for messages
                print("Waiting for messages (10 seconds)...")
                time.sleep(10)
                
                mqtt_client.disconnect()
                print("✓ Disconnected from MQTT broker")
                
            else:
                print("✗ Failed to connect to MQTT broker")
                return 1
        else:
            print("Use --test to run test mode")
    
    except KeyboardInterrupt:
        print("\nMQTT client interrupted")
        mqtt_client.disconnect()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
