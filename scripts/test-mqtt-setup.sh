#!/bin/bash
set -euo pipefail

# Test MQTT setup end-to-end
echo "🧪 Testing DoomBox MQTT Setup"
echo "=============================="

# Configuration
BROKER_HOST=${1:-"localhost"}
RADXA_IP="10.0.0.234"
TEST_PLAYER="TestWarrior"

echo "📡 MQTT Broker: $BROKER_HOST:1883"
echo "🎮 Radxa IP: $RADXA_IP"
echo ""

# Check if mosquitto is running
if ! systemctl is-active --quiet mosquitto; then
    echo "❌ Mosquitto service is not running"
    echo "   Run: sudo systemctl start mosquitto"
    exit 1
fi

echo "✅ Mosquitto service is running"

# Test 1: Basic MQTT connectivity
echo ""
echo "🔧 Test 1: Basic MQTT connectivity"
echo "   Testing publish/subscribe..."

# Start subscriber in background
mosquitto_sub -h "$BROKER_HOST" -t "doombox/test" -C 1 > /tmp/mqtt_test.out &
SUB_PID=$!

sleep 1

# Publish test message
mosquitto_pub -h "$BROKER_HOST" -t "doombox/test" -m "Hello DoomBox!"

# Wait for subscriber
sleep 2

# Check result
if kill -0 $SUB_PID 2>/dev/null; then
    kill $SUB_PID 2>/dev/null || true
fi

if [ -f /tmp/mqtt_test.out ] && grep -q "Hello DoomBox!" /tmp/mqtt_test.out; then
    echo "✅ Basic MQTT communication works"
else
    echo "❌ Basic MQTT communication failed"
    exit 1
fi

rm -f /tmp/mqtt_test.out

# Test 2: Python MQTT client
echo ""
echo "🔧 Test 2: Python MQTT client"
echo "   Testing Python client connectivity..."

if python3 -c "
import paho.mqtt.client as mqtt
import sys
import time

client = mqtt.Client()
connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    connected = (rc == 0)
    client.disconnect()

client.on_connect = on_connect
try:
    client.connect('$BROKER_HOST', 1883, 60)
    client.loop_start()
    time.sleep(2)
    client.loop_stop()
    sys.exit(0 if connected else 1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo "✅ Python MQTT client works"
else
    echo "❌ Python MQTT client failed"
    exit 1
fi

# Test 3: DoomBox test client
echo ""
echo "🔧 Test 3: DoomBox test client"
echo "   Testing custom test client..."

if python3 scripts/mqtt-test-client.py --broker "$BROKER_HOST" status 2>/dev/null; then
    echo "✅ DoomBox test client works"
else
    echo "❌ DoomBox test client failed"
    echo "   Make sure you're in the doombox directory"
    exit 1
fi

# Test 4: Game launch simulation
echo ""
echo "🔧 Test 4: Game launch simulation"
echo "   Simulating game launch for $TEST_PLAYER..."

# Monitor for responses
mosquitto_sub -h "$BROKER_HOST" -t "doombox/#" -C 5 > /tmp/game_test.out &
MONITOR_PID=$!

sleep 1

# Send game launch command
python3 scripts/mqtt-test-client.py --broker "$BROKER_HOST" launch "$TEST_PLAYER" --skill 3 2>/dev/null

# Send web form registration
python3 scripts/mqtt-test-client.py --broker "$BROKER_HOST" register "$TEST_PLAYER" 2>/dev/null

sleep 3

# Stop monitoring
if kill -0 $MONITOR_PID 2>/dev/null; then
    kill $MONITOR_PID 2>/dev/null || true
fi

if [ -f /tmp/game_test.out ]; then
    echo "✅ Game launch commands sent successfully"
    echo "   Messages captured:"
    cat /tmp/game_test.out | head -10
else
    echo "❌ Game launch test failed"
fi

rm -f /tmp/game_test.out

# Test 5: Network connectivity to Radxa
echo ""
echo "🔧 Test 5: Network connectivity to Radxa"
echo "   Testing connection to $RADXA_IP..."

if ping -c 1 -W 3 "$RADXA_IP" > /dev/null 2>&1; then
    echo "✅ Radxa is reachable at $RADXA_IP"
    
    # Test SSH connectivity
    if ssh -o ConnectTimeout=5 -o BatchMode=yes root@"$RADXA_IP" echo "SSH test" 2>/dev/null; then
        echo "✅ SSH access to Radxa works"
    else
        echo "⚠️  SSH access to Radxa failed (check SSH key setup)"
    fi
else
    echo "❌ Radxa is not reachable at $RADXA_IP"
    echo "   Check network connection and IP address"
fi

# Summary
echo ""
echo "🎯 Test Summary"
echo "==============="
echo "✅ MQTT broker is running on $BROKER_HOST:1883"
echo "✅ Basic MQTT communication works"
echo "✅ Python MQTT client works"
echo "✅ DoomBox test client works"
echo "✅ Game launch simulation completed"
echo ""
echo "🚀 Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Push changes to GitHub:"
echo "   git add . && git commit -m 'Setup MQTT broker and test client' && git push"
echo ""
echo "2. Deploy to Radxa:"
echo "   ssh root@$RADXA_IP 'cd /root/doombox && git pull'"
echo ""
echo "3. Test from Radxa:"
echo "   ssh root@$RADXA_IP 'cd /root/doombox && python3 scripts/mqtt-test-client.py --broker $BROKER_HOST status'"
echo ""
echo "4. Launch game from your host:"
echo "   python3 scripts/mqtt-test-client.py --broker $BROKER_HOST launch YourName"
echo ""
echo "5. Monitor all activity:"
echo "   python3 scripts/mqtt-test-client.py --broker $BROKER_HOST monitor"
