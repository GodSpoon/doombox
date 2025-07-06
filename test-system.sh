#!/bin/bash
# DoomBox System Test Script
# Tests all components to ensure they're working properly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo -e "  DoomBox System Test"
echo -e "==========================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Function to run test with status
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name FAILED${NC}"
        return 1
    fi
}

# Function to check if command exists
check_command() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if file exists
check_file() {
    [ -f "$1" ]
}

# Function to check if directory exists
check_directory() {
    [ -d "$1" ]
}

# Test Results
PASSED=0
FAILED=0

echo -e "${BLUE}1. Testing System Dependencies${NC}"

# System commands
for cmd in "python3" "pip3" "dsda-doom" "bluetoothctl" "sqlite3" "xset" "unclutter"; do
    if run_test "Command: $cmd" "check_command $cmd"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo -e "\n${BLUE}2. Testing File Structure${NC}"

# Required files
files=(
    "$SCRIPT_DIR/src/kiosk-manager.py"
    "$SCRIPT_DIR/src/controller-input.py"
    "$SCRIPT_DIR/src/game-launcher.py"
    "$SCRIPT_DIR/requirements.txt"
    "$SCRIPT_DIR/start-kiosk.sh"
    "$SCRIPT_DIR/configure-dietpi-autologin.sh"
    "$SCRIPT_DIR/doombox-kiosk.service"
)

for file in "${files[@]}"; do
    if run_test "File: $(basename $file)" "check_file $file"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo -e "\n${BLUE}3. Testing Directory Structure${NC}"

# Required directories
directories=(
    "$SCRIPT_DIR/src"
    "$SCRIPT_DIR/config"
    "$SCRIPT_DIR/fonts"
    "$SCRIPT_DIR/vid"
    "$SCRIPT_DIR/logs"
)

for dir in "${directories[@]}"; do
    if run_test "Directory: $(basename $dir)" "check_directory $dir"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo -e "\n${BLUE}4. Testing Python Dependencies${NC}"

# Python modules
modules=("pygame" "qrcode" "sqlite3" "cv2" "numpy" "requests")

for module in "${modules[@]}"; do
    if run_test "Python module: $module" "python3 -c 'import $module' 2>/dev/null"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo -e "\n${BLUE}5. Testing Game Dependencies${NC}"

# Game files
if run_test "DOOM WAD file" "check_file /usr/share/games/doom/doom1.wad"; then
    ((PASSED++))
else
    ((FAILED++))
fi

if run_test "dsda-doom executable" "dsda-doom -help >/dev/null 2>&1"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo -e "\n${BLUE}6. Testing Scripts${NC}"

# Script executability
scripts=("$SCRIPT_DIR/start-kiosk.sh" "$SCRIPT_DIR/configure-dietpi-autologin.sh")

for script in "${scripts[@]}"; do
    if run_test "Executable: $(basename $script)" "[ -x $script ]"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo -e "\n${BLUE}7. Testing Configuration${NC}"

# Python script syntax
python_scripts=("$SCRIPT_DIR/src/kiosk-manager.py" "$SCRIPT_DIR/src/controller-input.py" "$SCRIPT_DIR/src/game-launcher.py")

for script in "${python_scripts[@]}"; do
    if run_test "Python syntax: $(basename $script)" "python3 -m py_compile $script"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo -e "\n${BLUE}8. Testing System Services${NC}"

# Bluetooth service
if run_test "Bluetooth service" "systemctl is-active bluetooth >/dev/null 2>&1 || systemctl is-enabled bluetooth >/dev/null 2>&1"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# X11 availability (if running in X11 environment)
if [ -n "$DISPLAY" ]; then
    if run_test "X11 display" "xset q >/dev/null 2>&1"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}Skipping X11 test (not in X11 environment)${NC}"
fi

echo -e "\n${BLUE}9. Testing Functional Components${NC}"

# Game launcher test
if run_test "Game launcher" "python3 $SCRIPT_DIR/src/game-launcher.py --test"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Controller scanner test
if run_test "Controller scanner" "timeout 5 python3 $SCRIPT_DIR/src/controller-input.py --status"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Database creation test
if run_test "Database creation" "python3 -c 'import sqlite3; conn = sqlite3.connect(\"$SCRIPT_DIR/test.db\"); conn.execute(\"CREATE TABLE test (id INTEGER)\"); conn.close()' && rm -f $SCRIPT_DIR/test.db"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo -e "\n${GREEN}=========================================="
echo -e "  Test Results Summary"
echo -e "==========================================${NC}"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! DoomBox is ready to go!${NC}"
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo -e "1. Run: sudo ./configure-dietpi-autologin.sh"
    echo -e "2. Reboot the system"
    echo -e "3. The kiosk should start automatically"
    echo -e "4. Set up MQTT server on another host"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please fix the issues above.${NC}"
    echo -e "\n${YELLOW}Common fixes:${NC}"
    echo -e "1. Install missing dependencies: sudo apt install <package>"
    echo -e "2. Install Python packages: pip3 install -r requirements.txt"
    echo -e "3. Check file permissions: chmod +x script.sh"
    echo -e "4. Verify file paths and locations"
    exit 1
fi
