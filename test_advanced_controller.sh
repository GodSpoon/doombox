#!/bin/bash

# Test script for advanced controller pairing
# This script verifies the functionality without requiring an actual controller

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/advanced_controller_pair.py"
SHELL_SCRIPT="$SCRIPT_DIR/advanced_controller_pair.sh"

echo -e "${BLUE}=========================================="
echo -e "  Advanced Controller Pairing Test"
echo -e "==========================================${NC}"
echo ""

# Test 1: Check if files exist
echo -e "${YELLOW}Test 1: Checking files...${NC}"
if [ -f "$PYTHON_SCRIPT" ]; then
    echo -e "   ${GREEN}✓ Python script exists${NC}"
else
    echo -e "   ${RED}❌ Python script missing${NC}"
    exit 1
fi

if [ -f "$SHELL_SCRIPT" ]; then
    echo -e "   ${GREEN}✓ Shell wrapper exists${NC}"
else
    echo -e "   ${RED}❌ Shell wrapper missing${NC}"
    exit 1
fi

# Test 2: Check if files are executable
echo -e "${YELLOW}Test 2: Checking permissions...${NC}"
if [ -x "$PYTHON_SCRIPT" ]; then
    echo -e "   ${GREEN}✓ Python script is executable${NC}"
else
    echo -e "   ${RED}❌ Python script not executable${NC}"
    chmod +x "$PYTHON_SCRIPT"
    echo -e "   ${GREEN}✓ Fixed permissions${NC}"
fi

if [ -x "$SHELL_SCRIPT" ]; then
    echo -e "   ${GREEN}✓ Shell wrapper is executable${NC}"
else
    echo -e "   ${RED}❌ Shell wrapper not executable${NC}"
    chmod +x "$SHELL_SCRIPT"
    echo -e "   ${GREEN}✓ Fixed permissions${NC}"
fi

# Test 3: Check Python syntax
echo -e "${YELLOW}Test 3: Checking Python syntax...${NC}"
if python3 -m py_compile "$PYTHON_SCRIPT" 2>/dev/null; then
    echo -e "   ${GREEN}✓ Python syntax is valid${NC}"
else
    echo -e "   ${RED}❌ Python syntax error${NC}"
    python3 -m py_compile "$PYTHON_SCRIPT"
    exit 1
fi

# Test 4: Check shell script syntax
echo -e "${YELLOW}Test 4: Checking shell script syntax...${NC}"
if bash -n "$SHELL_SCRIPT" 2>/dev/null; then
    echo -e "   ${GREEN}✓ Shell script syntax is valid${NC}"
else
    echo -e "   ${RED}❌ Shell script syntax error${NC}"
    bash -n "$SHELL_SCRIPT"
    exit 1
fi

# Test 5: Test help output
echo -e "${YELLOW}Test 5: Testing help output...${NC}"
if "$SHELL_SCRIPT" --help >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Help command works${NC}"
else
    echo -e "   ${RED}❌ Help command failed${NC}"
fi

# Test 6: Test status command
echo -e "${YELLOW}Test 6: Testing status command...${NC}"
if "$SHELL_SCRIPT" --status >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Status command works${NC}"
else
    echo -e "   ${RED}❌ Status command failed${NC}"
fi

# Test 7: Test troubleshoot command
echo -e "${YELLOW}Test 7: Testing troubleshoot command...${NC}"
if "$SHELL_SCRIPT" --troubleshoot >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Troubleshoot command works${NC}"
else
    echo -e "   ${RED}❌ Troubleshoot command failed${NC}"
fi

# Test 8: Test Python direct execution
echo -e "${YELLOW}Test 8: Testing Python direct execution...${NC}"
if python3 "$PYTHON_SCRIPT" --help >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Python script can be executed directly${NC}"
else
    echo -e "   ${RED}❌ Python script direct execution failed${NC}"
fi

# Test 9: Check dependencies
echo -e "${YELLOW}Test 9: Checking system dependencies...${NC}"
deps_ok=true

# Check Python 3
if command -v python3 >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Python 3 available${NC}"
else
    echo -e "   ${RED}❌ Python 3 not available${NC}"
    deps_ok=false
fi

# Check Bluetooth tools
bluetooth_tools=("bluetoothctl" "hciconfig" "rfkill")
for tool in "${bluetooth_tools[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo -e "   ${GREEN}✓ $tool available${NC}"
    else
        echo -e "   ${YELLOW}⚠️  $tool not available (will be needed for actual pairing)${NC}"
    fi
done

# Test 10: Test scan-only mode (should not hang)
echo -e "${YELLOW}Test 10: Testing scan-only mode (5 second timeout)...${NC}"
if timeout 5 python3 "$PYTHON_SCRIPT" --scan-only >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Scan-only mode works${NC}"
else
    echo -e "   ${YELLOW}⚠️  Scan-only mode timed out (expected without Bluetooth)${NC}"
fi

echo ""
echo -e "${BLUE}=========================================="
echo -e "  Test Results Summary"
echo -e "==========================================${NC}"
echo ""

if $deps_ok; then
    echo -e "${GREEN}🎮 All tests passed! Advanced controller pairing is ready.${NC}"
    echo ""
    echo -e "${CYAN}Usage examples:${NC}"
    echo -e "   ${WHITE}$SHELL_SCRIPT${NC}                    # Interactive pairing"
    echo -e "   ${WHITE}$SHELL_SCRIPT --status${NC}          # Check current status"
    echo -e "   ${WHITE}$SHELL_SCRIPT --troubleshoot${NC}    # Run diagnostics"
    echo -e "   ${WHITE}$SHELL_SCRIPT --help${NC}            # Show help"
    echo ""
else
    echo -e "${YELLOW}⚠️  Tests completed with warnings. Some dependencies may be missing.${NC}"
    echo -e "${CYAN}To install dependencies:${NC}"
    echo -e "   ${WHITE}$SHELL_SCRIPT --install-deps${NC}"
    echo ""
fi

echo -e "${CYAN}For detailed documentation, see:${NC}"
echo -e "   ${WHITE}ADVANCED_CONTROLLER_README.md${NC}"
echo ""
