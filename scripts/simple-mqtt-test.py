#!/usr/bin/env python3
"""
Simple MQTT Game Trigger Test
Tests direct MQTT command handling without complex imports
"""

import sys
import os
import time
import json
import subprocess

# Change to the doombox directory
os.chdir('/root/doombox' if os.path.exists('/root/doombox') else '/home/sam/SPOON_GIT/doombox')

def test_mqtt_command_trigger():
    """Test if we can trigger a game launch via MQTT"""
    print("🎮 Testing MQTT Game Launch Trigger")
    print("=" * 40)
    
    try:
        # Import the MQTT client directly
        sys.path.append('.')
        sys.path.append('./src')
        
        # Try to run the MQTT client test
        from scripts.mqtt_test_client import DoomBoxTestClient
        
        # Get the broker IP from config
        try:
            exec(open('config/config.py').read())
            broker_ip = MQTT_BROKER
            broker_port = MQTT_PORT
        except:
            broker_ip = "10.0.0.215"
            broker_port = 1883
        
        print(f"📡 Connecting to MQTT broker at {broker_ip}:{broker_port}")
        
        # Create test client
        client = DoomBoxTestClient(broker_ip, broker_port)
        
        if client.connect():
            print("✅ Connected to MQTT broker")
            
            # Send a test launch command
            print("🎮 Sending game launch command...")
            success = client.send_launch_game("DirectTestPlayer", 3)
            
            if success:
                print("✅ Game launch command sent successfully")
                
                # Wait a bit for response
                print("⏱️  Waiting for response...")
                time.sleep(3)
                
                print("✅ Test completed successfully")
                result = True
            else:
                print("❌ Failed to send game launch command")
                result = False
            
            client.disconnect()
        else:
            print("❌ Failed to connect to MQTT broker")
            result = False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        result = False
    
    return result

def test_kiosk_mqtt_integration():
    """Test if the kiosk manager has MQTT integration"""
    print("\n🔧 Testing Kiosk MQTT Integration")
    print("=" * 40)
    
    try:
        # Check if kiosk manager exists and has MQTT integration
        with open('src/kiosk-manager.py', 'r') as f:
            kiosk_code = f.read()
        
        if 'mqtt' in kiosk_code.lower():
            print("✅ Kiosk manager contains MQTT code")
        else:
            print("❌ Kiosk manager does not contain MQTT code")
            return False
        
        if 'DoomBoxMQTTClient' in kiosk_code:
            print("✅ Kiosk manager imports MQTT client")
        else:
            print("❌ Kiosk manager does not import MQTT client")
            return False
        
        if 'setup_game_integration' in kiosk_code:
            print("✅ Kiosk manager has game integration setup")
        else:
            print("❌ Kiosk manager missing game integration setup")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Kiosk integration test failed: {e}")
        return False

def test_direct_launch():
    """Test if we can launch the game directly"""
    print("\n🎮 Testing Direct Game Launch")
    print("=" * 30)
    
    try:
        # Check if lzdoom is available
        result = subprocess.run(['which', 'lzdoom'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ lzdoom found at:", result.stdout.strip())
        else:
            print("❌ lzdoom not found in PATH")
            
            # Check common locations
            common_paths = ['/usr/games/lzdoom', '/usr/local/bin/lzdoom', '/usr/bin/lzdoom']
            found = False
            for path in common_paths:
                if os.path.exists(path):
                    print(f"✅ lzdoom found at: {path}")
                    found = True
                    break
            
            if not found:
                print("❌ lzdoom not found in common locations")
                return False
        
        # Check if DOOM.WAD exists
        wad_paths = [
            '/opt/doombox/doom/DOOM.WAD',
            './doom/DOOM.WAD',
            '/root/doombox/doom/DOOM.WAD'
        ]
        
        wad_found = False
        for wad_path in wad_paths:
            if os.path.exists(wad_path):
                print(f"✅ DOOM.WAD found at: {wad_path}")
                wad_found = True
                break
        
        if not wad_found:
            print("❌ DOOM.WAD not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Direct launch test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Simple MQTT Game Trigger Test")
    print("=" * 50)
    
    tests = [
        test_kiosk_mqtt_integration,
        test_mqtt_command_trigger,
        test_direct_launch
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        print("\n💡 Next steps:")
        print("1. Ensure kiosk manager has MQTT integration")
        print("2. Start kiosk manager with MQTT enabled")
        print("3. Test game launch via MQTT")
        return 1

if __name__ == "__main__":
    sys.exit(main())
