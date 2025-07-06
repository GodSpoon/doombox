#!/bin/bash
set -euo pipefail

# Configure MQTT broker IP automatically
echo "🔧 Configuring MQTT broker IP..."

# Get the current host IP on the local network
HOST_IP=$(ip route get 1 | grep -oP 'src \K\S+' | head -1)

if [ -z "$HOST_IP" ]; then
    # Fallback method
    HOST_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -1)
fi
RADXA_IP="10.0.0.234"

if [ -z "$HOST_IP" ]; then
    echo "❌ Could not determine host IP address"
    exit 1
fi

echo "🏠 Detected host IP: $HOST_IP"
echo "🎮 Radxa IP: $RADXA_IP"

# Update config.py with the correct IP
CONFIG_FILE="/home/sam/SPOON_GIT/doombox/config/config.py"

if [ -f "$CONFIG_FILE" ]; then
    echo "📝 Updating config.py with MQTT broker IP..."
    
    # Use sed to replace the IP in the config file
    sed -i "s/MQTT_BROKER = \"10\.0\.0\.100\"/MQTT_BROKER = \"$HOST_IP\"/" "$CONFIG_FILE"
    
    echo "✅ Updated MQTT_BROKER in config.py to: $HOST_IP"
else
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Update webhook.py with the correct IP
WEBHOOK_FILE="/home/sam/SPOON_GIT/doombox/webhook.py"

if [ -f "$WEBHOOK_FILE" ]; then
    echo "📝 Updating webhook.py with MQTT broker IP..."
    
    # Update the fallback IP in webhook.py
    sed -i "s/MQTT_BROKER = \"10\.0\.0\.100\"/MQTT_BROKER = \"$HOST_IP\"/" "$WEBHOOK_FILE"
    
    echo "✅ Updated webhook.py MQTT broker IP to: $HOST_IP"
else
    echo "❌ Webhook file not found: $WEBHOOK_FILE"
    exit 1
fi

echo ""
echo "🎯 Configuration Summary:"
echo "  - MQTT Broker (your Arch host): $HOST_IP:1883"
echo "  - DoomBox Kiosk (Radxa): $RADXA_IP"
echo ""
echo "🚀 Next steps:"
echo "  1. Run: ./scripts/setup-mqtt-broker.sh"
echo "  2. Test locally: python3 scripts/mqtt-test-client.py status"
echo "  3. Push to GitHub and pull on Radxa"
echo "  4. Test from Radxa: python3 scripts/mqtt-test-client.py --broker $HOST_IP status"
echo ""
echo "💡 Test command examples:"
echo "  # Launch game for player 'TestPlayer'"
echo "  python3 scripts/mqtt-test-client.py --broker $HOST_IP launch TestPlayer"
echo ""
echo "  # Monitor all messages"
echo "  python3 scripts/mqtt-test-client.py --broker $HOST_IP monitor"
echo ""
echo "  # Interactive mode"
echo "  python3 scripts/mqtt-test-client.py --broker $HOST_IP interactive"
