#!/bin/bash
# DoomBox Test Suite
# Comprehensive testing for all DoomBox components

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}=========================================="
echo -e "  DoomBox Test Suite"
echo -e "==========================================${NC}"
echo ""

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}Test: $test_name${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if eval "$test_command"; then
        echo -e "   ${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "   ${RED}❌ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

test_file_structure() {
    echo -e "${CYAN}Testing file structure...${NC}"
    
    # Check required directories
    local required_dirs=("src" "config" "scripts" "web" "assets" "logs")
    for dir in "${required_dirs[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            echo -e "   ${GREEN}✓ Directory exists: $dir${NC}"
        else
            echo -e "   ${RED}❌ Missing directory: $dir${NC}"
            return 1
        fi
    done
    
    # Check key files
    local key_files=(
        "src/controller-input.py"
        "src/kiosk-manager.py"
        "scripts/controller-manager.sh"
        "web/index.html"
        "config/config.py"
        "setup.sh"
        "uninstall.sh"
    )
    
    for file in "${key_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo -e "   ${GREEN}✓ File exists: $file${NC}"
        else
            echo -e "   ${RED}❌ Missing file: $file${NC}"
            return 1
        fi
    done
    
    return 0
}

test_python_syntax() {
    echo -e "${CYAN}Testing Python syntax...${NC}"
    
    local python_files=()
    mapfile -t python_files < <(find "$PROJECT_ROOT" -name "*.py" -type f)
    
    for file in "${python_files[@]}"; do
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "   ${GREEN}✓ Valid syntax: $(basename "$file")${NC}"
        else
            echo -e "   ${RED}❌ Syntax error: $(basename "$file")${NC}"
            return 1
        fi
    done
    
    return 0
}

test_shell_syntax() {
    echo -e "${CYAN}Testing shell script syntax...${NC}"
    
    local shell_files=()
    mapfile -t shell_files < <(find "$PROJECT_ROOT" -name "*.sh" -type f)
    
    for file in "${shell_files[@]}"; do
        if bash -n "$file" 2>/dev/null; then
            echo -e "   ${GREEN}✓ Valid syntax: $(basename "$file")${NC}"
        else
            echo -e "   ${RED}❌ Syntax error: $(basename "$file")${NC}"
            return 1
        fi
    done
    
    return 0
}

test_permissions() {
    echo -e "${CYAN}Testing file permissions...${NC}"
    
    local executable_files=(
        "setup.sh"
        "uninstall.sh"
        "src/controller-input.py"
        "src/kiosk-manager.py"
        "scripts/controller-manager.sh"
    )
    
    for file in "${executable_files[@]}"; do
        if [ -x "$PROJECT_ROOT/$file" ]; then
            echo -e "   ${GREEN}✓ Executable: $file${NC}"
        else
            echo -e "   ${YELLOW}⚠ Making executable: $file${NC}"
            chmod +x "$PROJECT_ROOT/$file"
        fi
    done
    
    return 0
}

test_dependencies() {
    echo -e "${CYAN}Testing system dependencies...${NC}"
    
    local required_commands=("python3" "bash" "systemctl")
    
    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo -e "   ${GREEN}✓ Found: $cmd${NC}"
        else
            echo -e "   ${RED}❌ Missing: $cmd${NC}"
            return 1
        fi
    done
    
    return 0
}

test_controller_module() {
    echo -e "${CYAN}Testing controller module...${NC}"
    
    # Test help output
    if python3 "$PROJECT_ROOT/src/controller-input.py" --help >/dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Controller module help works${NC}"
    else
        echo -e "   ${RED}❌ Controller module help failed${NC}"
        return 1
    fi
    
    # Test status command (should work without hardware)
    if python3 "$PROJECT_ROOT/src/controller-input.py" --status >/dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Controller status command works${NC}"
    else
        echo -e "   ${YELLOW}⚠ Controller status command failed (may be expected without hardware)${NC}"
    fi
    
    return 0
}

test_controller_script() {
    echo -e "${CYAN}Testing controller script...${NC}"
    
    # Test help output
    if bash "$PROJECT_ROOT/scripts/controller-manager.sh" --help >/dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Controller script help works${NC}"
    else
        echo -e "   ${RED}❌ Controller script help failed${NC}"
        return 1
    fi
    
    return 0
}

test_cleanup() {
    echo -e "${CYAN}Testing cleanup...${NC}"
    
    # Check for redundant files that should be removed
    local redundant_files=(
        "advanced_controller_pair.py"
        "advanced_controller_pair.sh"
        "pair_controller.sh"
        "debug_controller.sh"
        "controller_overview.sh"
        "setup_controller.sh"
        "test_advanced_controller.sh"
        "auto_connect_controller.sh"
        "ADVANCED_CONTROLLER_README.md"
        "ADVANCED_CONTROLLER_SUMMARY.md"
        "CONTROLLER_README.md"
        "filetree.json"
    )
    
    local found_redundant=false
    for file in "${redundant_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo -e "   ${YELLOW}⚠ Redundant file still exists: $file${NC}"
            found_redundant=true
        fi
    done
    
    if [ "$found_redundant" = false ]; then
        echo -e "   ${GREEN}✓ No redundant files found${NC}"
    else
        echo -e "   ${YELLOW}⚠ Some redundant files should be removed${NC}"
    fi
    
    return 0
}

# Run all tests
main() {
    echo -e "${BLUE}Running comprehensive test suite...${NC}"
    echo ""
    
    run_test "File Structure" "test_file_structure"
    run_test "Python Syntax" "test_python_syntax"
    run_test "Shell Syntax" "test_shell_syntax"
    run_test "File Permissions" "test_permissions"
    run_test "System Dependencies" "test_dependencies"
    run_test "Controller Module" "test_controller_module"
    run_test "Controller Script" "test_controller_script"
    run_test "Cleanup Status" "test_cleanup"
    
    # Final summary
    echo -e "${BLUE}=========================================="
    echo -e "  Test Results"
    echo -e "==========================================${NC}"
    echo -e "Tests Run:    $TESTS_RUN"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        exit 1
    fi
}

main "$@"
