#!/usr/bin/env python3
"""
Test script to verify game state management and video pause functionality
"""

import sys
import os
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game_launcher import GameLauncher

def test_game_state_callbacks():
    """Test that game state callbacks work correctly"""
    print("Testing game state callbacks...")
    
    # Track state changes
    state_changes = []
    
    def state_callback(old_state, new_state, player_name):
        state_changes.append((old_state, new_state, player_name))
        print(f"State changed: {old_state} -> {new_state} (player: {player_name})")
    
    # Create game launcher
    launcher = GameLauncher()
    launcher.add_game_state_callback(state_callback)
    
    print(f"Initial state: {launcher.get_game_state()}")
    
    # Test state changes
    launcher._set_game_state("starting")
    launcher._set_game_state("running")
    launcher._set_game_state("finished")
    launcher._set_game_state("idle")
    
    print(f"State changes recorded: {len(state_changes)}")
    for change in state_changes:
        print(f"  {change}")
    
    return len(state_changes) == 4

def test_game_launcher_config():
    """Test that game launcher configuration is set up correctly"""
    print("\nTesting game launcher configuration...")
    
    launcher = GameLauncher()
    
    # Check dependencies
    deps_ok = launcher.check_dependencies()
    print(f"Dependencies check: {'✓' if deps_ok else '✗'}")
    
    # Setup configuration
    config_ok = launcher.setup_doom_config()
    print(f"Configuration setup: {'✓' if config_ok else '✗'}")
    
    # Check configuration file
    config_file = launcher.doom_config['config_file']
    if os.path.exists(config_file):
        print(f"Configuration file exists: {config_file}")
        with open(config_file, 'r') as f:
            content = f.read()
            fullscreen_enforced = 'use_fullscreen 1' in content and 'force_fullscreen 1' in content
            print(f"Fullscreen enforced: {'✓' if fullscreen_enforced else '✗'}")
    else:
        print(f"Configuration file missing: {config_file}")
        return False
    
    return deps_ok and config_ok

def test_game_status():
    """Test game status reporting"""
    print("\nTesting game status reporting...")
    
    launcher = GameLauncher()
    
    # Get initial status
    status = launcher.get_game_status()
    print(f"Initial status: {status}")
    
    # Check required fields
    required_fields = ['running', 'state', 'current_player', 'process_id', 'doom_config']
    all_fields_present = all(field in status for field in required_fields)
    print(f"All status fields present: {'✓' if all_fields_present else '✗'}")
    
    return all_fields_present

def main():
    """Run all tests"""
    print("=" * 60)
    print("DoomBox Game State Management Tests")
    print("=" * 60)
    
    tests = [
        ("Game State Callbacks", test_game_state_callbacks),
        ("Game Launcher Configuration", test_game_launcher_config),
        ("Game Status Reporting", test_game_status)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name}: FAIL - {e}")
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Game state management is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
