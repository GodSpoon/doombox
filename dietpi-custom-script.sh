#!/bin/bash
# DietPi-AutoStart custom script
# Location: /var/lib/dietpi/dietpi-autostart/custom.sh

# Set up environment
export DISPLAY=:0
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

# Colors for logging
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Log function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] DoomBox:${NC} $1" | tee -a /var/log/doombox-autostart.log
}

log "Starting DoomBox kiosk via DietPi AutoStart"

# Change to doombox directory
cd /root/doombox

# Wait for system to be ready
sleep 10

# Setup display if we're in graphical mode
if [ -n "$DISPLAY" ]; then
    log "Setting up display..."
    xset s off 2>/dev/null || true
    xset -dpms 2>/dev/null || true
    xset s noblank 2>/dev/null || true
    unclutter -idle 1 -root &>/dev/null &
fi

# Setup Bluetooth for controller
log "Starting Bluetooth service..."
systemctl start bluetooth 2>/dev/null || true

# Auto-connect controller if configured
if [ -f "/root/doombox/config/controller.json" ]; then
    log "Auto-connecting controller..."
    python3 /root/doombox/src/controller-input.py --auto-connect --verbose &>/dev/null &
fi

# Start the kiosk application
log "Launching DoomBox kiosk..."
exec /root/doombox/start-kiosk.sh
