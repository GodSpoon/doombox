#!/bin/bash
set -euo pipefail

# Deploy DoomBox MQTT updates to Radxa
echo "🚀 Deploying DoomBox MQTT updates to Radxa..."

RADXA_IP="10.0.0.234"
HOST_IP=$(ip route get 1 | grep -oP 'src \K\S+' | head -1)

if [ -z "$HOST_IP" ]; then
    # Fallback method
    HOST_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -1)
fi

echo "🏠 Host IP: $HOST_IP"
echo "🎮 Radxa IP: $RADXA_IP"

# Step 1: Configure IP addresses
echo ""
echo "🔧 Step 1: Configuring IP addresses..."
./scripts/configure-mqtt-ip.sh

# Step 2: Commit and push changes
echo ""
echo "🔧 Step 2: Committing and pushing changes..."
git add .
git commit -m "Setup MQTT broker and test client - IP: $HOST_IP" || echo "No changes to commit"
git push

# Step 3: Deploy to Radxa
echo ""
echo "🔧 Step 3: Deploying to Radxa..."
if ssh -o ConnectTimeout=5 root@"$RADXA_IP" "cd /root/doombox && git pull"; then
    echo "✅ Successfully pulled updates on Radxa"
else
    echo "❌ Failed to pull updates on Radxa"
    echo "   Check SSH connection and try manually:"
    echo "   ssh root@$RADXA_IP 'cd /root/doombox && git pull'"
    exit 1
fi

# Step 4: Install Python dependencies on Radxa
echo ""
echo "🔧 Step 4: Installing Python dependencies on Radxa..."
if ssh root@"$RADXA_IP" "cd /root/doombox && pip3 install paho-mqtt flask"; then
    echo "✅ Dependencies installed on Radxa"
else
    echo "⚠️  Failed to install dependencies on Radxa"
    echo "   Try manually: ssh root@$RADXA_IP 'pip3 install paho-mqtt flask'"
fi

# Step 5: Test connection
echo ""
echo "🔧 Step 5: Testing MQTT connection from Radxa..."
if ssh root@"$RADXA_IP" "cd /root/doombox && python3 scripts/mqtt-test-client.py --broker $HOST_IP status"; then
    echo "✅ MQTT connection test successful!"
else
    echo "❌ MQTT connection test failed"
    echo "   Check that mosquitto is running on your host:"
    echo "   systemctl status mosquitto"
fi

echo ""
echo "🎯 Deployment complete!"
echo ""
echo "🧪 Test commands:"
echo "  # From your host - launch game on Radxa:"
echo "  python3 scripts/mqtt-test-client.py --broker $HOST_IP launch TestPlayer"
echo ""
echo "  # From Radxa - get status:"
echo "  ssh root@$RADXA_IP 'cd /root/doombox && python3 scripts/mqtt-test-client.py --broker $HOST_IP status'"
echo ""
echo "  # Monitor all activity:"
echo "  python3 scripts/mqtt-test-client.py --broker $HOST_IP monitor"
echo ""
echo "🎮 Ready to launch games remotely!"
