#!/bin/bash
set -euo pipefail

# Setup MQTT broker on Arch Linux host
echo "🔧 Setting up MQTT broker on Arch Linux..."

# Install mosquitto (MQTT broker)
if ! command -v mosquitto &> /dev/null; then
    echo "Installing mosquitto..."
    sudo pacman -S mosquitto --noconfirm
fi

# Install mosquitto clients for testing
if ! command -v mosquitto_pub &> /dev/null; then
    echo "Installing mosquitto clients..."
    sudo pacman -S mosquitto-clients --noconfirm
fi

# Create mosquitto configuration directory
sudo mkdir -p /etc/mosquitto/conf.d

# Create basic configuration
sudo tee /etc/mosquitto/conf.d/doombox.conf > /dev/null << 'EOF'
# DoomBox MQTT Configuration
listener 1883
allow_anonymous true
log_dest stdout
log_type error
log_type warning
log_type notice
log_type information
connection_messages true
log_timestamp true
EOF

# Enable and start mosquitto service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Check if mosquitto is running
if sudo systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto MQTT broker is running"
    
    # Get system IP
    HOST_IP=$(ip route get 1 | grep -oP 'src \K\S+' | head -1)
    
    if [ -z "$HOST_IP" ]; then
        # Fallback method
        HOST_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -1)
    fi
    echo "📡 MQTT broker listening on: $HOST_IP:1883"
    
    # Test the broker
    echo "🧪 Testing MQTT broker..."
    
    # Test publish/subscribe
    mosquitto_pub -h localhost -t "doombox/test" -m "MQTT broker test message" &
    sleep 1
    
    echo "✅ MQTT broker setup complete!"
    echo ""
    echo "Configuration:"
    echo "  - Host: $HOST_IP"
    echo "  - Port: 1883"
    echo "  - Anonymous access: enabled"
    echo ""
    echo "Test commands:"
    echo "  mosquitto_pub -h $HOST_IP -t 'doombox/test' -m 'Hello DoomBox'"
    echo "  mosquitto_sub -h $HOST_IP -t 'doombox/#'"
    
else
    echo "❌ Failed to start mosquitto service"
    sudo systemctl status mosquitto
    exit 1
fi
