#!/bin/bash

# DoomBox Controller Auto-Connect Script
# Automatically connects to paired DualShock 4 controllers
# Designed for use in systemd services or startup scripts

# Configuration
CONTROLLER_CONFIG="$HOME/.doombox_controller"
LOG_FILE="/var/log/doombox_controller.log"
MAX_RETRIES=5
RETRY_DELAY=3
CONNECT_TIMEOUT=10

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$LOG_FILE"
}

# Load controller configuration
load_controller_config() {
    if [ -f "$CONTROLLER_CONFIG" ]; then
        source "$CONTROLLER_CONFIG"
        log_message "INFO" "Loaded controller config: $CONTROLLER_MAC"
        return 0
    else
        log_message "ERROR" "No controller configuration found at $CONTROLLER_CONFIG"
        return 1
    fi
}

# Check if controller is already connected
is_controller_connected() {
    if [ -n "$CONTROLLER_MAC" ]; then
        if bluetoothctl info "$CONTROLLER_MAC" 2>/dev/null | grep -q "Connected: yes"; then
            return 0
        fi
    fi
    return 1
}

# Connect to controller
connect_controller() {
    local retry=0
    
    while [ $retry -lt $MAX_RETRIES ]; do
        retry=$((retry + 1))
        log_message "INFO" "Connection attempt $retry/$MAX_RETRIES for $CONTROLLER_MAC"
        
        if timeout $CONNECT_TIMEOUT bluetoothctl connect "$CONTROLLER_MAC" 2>/dev/null; then
            log_message "INFO" "Controller connected successfully"
            return 0
        else
            log_message "WARN" "Connection attempt $retry failed"
            if [ $retry -lt $MAX_RETRIES ]; then
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    log_message "ERROR" "Failed to connect controller after $MAX_RETRIES attempts"
    return 1
}

# Main function
main() {
    log_message "INFO" "Starting DoomBox controller auto-connect"
    
    # Load controller configuration
    if ! load_controller_config; then
        log_message "ERROR" "Run pair_controller.sh first to set up controller"
        exit 1
    fi
    
    # Check if already connected
    if is_controller_connected; then
        log_message "INFO" "Controller already connected"
        exit 0
    fi
    
    # Try to connect
    if connect_controller; then
        log_message "INFO" "Controller auto-connect successful"
        exit 0
    else
        log_message "ERROR" "Controller auto-connect failed"
        exit 1
    fi
}

# Run main function
main "$@"
