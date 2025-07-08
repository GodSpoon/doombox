# DoomBox Makefile
# Simplified commands for common tasks

.PHONY: help setup test clean start install deps

# Default target
help:
	@echo "DoomBox - Available commands:"
	@echo ""
	@echo "  setup     - Run full setup (install deps, configure)"
	@echo "  start     - Start the kiosk"
	@echo "  test      - Run all tests"
	@echo "  test-mqtt - Test MQTT functionality only"
	@echo "  install   - Install Python dependencies"
	@echo "  clean     - Clean up logs and temporary files"
	@echo "  status    - Show system status"
	@echo ""

# Full setup
setup:
	@echo "🚀 Running DoomBox setup..."
	./setup.sh

# Start kiosk
start:
	@echo "🎮 Starting DoomBox kiosk..."
	./start-kiosk.sh

# Run all tests
test:
	@echo "🧪 Running all tests..."
	./tests/run_tests.py

# Test only MQTT
test-mqtt:
	@echo "🧪 Running MQTT tests..."
	./tests/mqtt/test_game_launch.py
	./tests/mqtt/test_mqtt_integration.py

# Install dependencies
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	rm -rf logs/*.log
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf config/__pycache__
	rm -f test_report.json
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Show status
status:
	@echo "📊 DoomBox Status"
	@echo "=================="
	@echo "Python version: $(shell python3 --version)"
	@echo "Project directory: $(PWD)"
	@echo "Tests available: $(shell find tests -name '*.py' | wc -l)"
	@echo "Source files: $(shell find src -name '*.py' | wc -l)"
	@echo ""
	@echo "Required commands:"
	@command -v python3 >/dev/null 2>&1 && echo "✅ python3" || echo "❌ python3"
	@command -v pygame >/dev/null 2>&1 && echo "✅ pygame" || echo "❌ pygame (pip install pygame)"
	@command -v dsda-doom >/dev/null 2>&1 && echo "✅ dsda-doom" || echo "❌ dsda-doom"
	@command -v bluetoothctl >/dev/null 2>&1 && echo "✅ bluetooth" || echo "❌ bluetooth"

# MQTT commands
mqtt-launch:
	@echo "🎮 Launching test game via MQTT..."
	./tools/mqtt_commands.py launch "TestPlayer" --skill 3

mqtt-stop:
	@echo "🛑 Stopping game via MQTT..."
	./tools/mqtt_commands.py stop

mqtt-status:
	@echo "📊 Requesting status via MQTT..."
	./tools/mqtt_commands.py status

# Controller commands
controller-scan:
	@echo "🎮 Scanning for controllers..."
	./scripts/controller-manager.sh scan

controller-test:
	@echo "🎮 Testing controller..."
	./scripts/controller-manager.sh test
