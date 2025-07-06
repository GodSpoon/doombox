#!/bin/bash
# DietPi-AutoStart custom script
# Location: /var/lib/dietpi/dietpi-autostart/custom.sh

# Set environment variables
export DISPLAY=:0

# Change to doombox directory
cd /root/doombox

# Log startup
echo "$(date): DietPi AutoStart launching DoomBox" >> /var/log/doombox-autostart.log

# Execute the DoomBox startup script
exec /root/doombox/start-kiosk.sh
