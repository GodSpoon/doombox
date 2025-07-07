#!/usr/bin/env python3
"""
Integration test for DoomBox game state management and video pause functionality
"""

import sys
import os
import time
import threading
import pygame

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MockVideoPlayer:
    """Mock video player for testing"""
    def __init__(self):
        self.running = False
        self.frame_count = 0
        
    def start(self):
        self.running = True
        return True
        
    def stop(self):
        self.running = False
        
    def get_frame(self):
        if self.running:
            self.frame_count += 1
            # Return a simple colored surface
            surface = pygame.Surface((1280, 960))
            surface.fill((50, 50, 100))  # Dark blue
            return surface
        return None
        
    def get_stats(self):
        return {'frames_played': self.frame_count}

def test_integration():
    """Test complete integration between kiosk, game launcher, and video player"""
    print("Testing DoomBox integration...")
    
    # Import after setting up path
    try:
        import importlib.util
        
        # Import kiosk-manager
        kiosk_spec = importlib.util.spec_from_file_location("kiosk_manager", 
                                                          os.path.join(os.path.dirname(__file__), "src", "kiosk-manager.py"))
        kiosk_module = importlib.util.module_from_spec(kiosk_spec)
        kiosk_spec.loader.exec_module(kiosk_module)
        DoomBoxKiosk = kiosk_module.DoomBoxKiosk
        
        # Import game-launcher
        game_spec = importlib.util.spec_from_file_location("game_launcher", 
                                                          os.path.join(os.path.dirname(__file__), "src", "game-launcher.py"))
        game_module = importlib.util.module_from_spec(game_spec)
        game_spec.loader.exec_module(game_module)
        GameLauncher = game_module.GameLauncher
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Module loading error: {e}")
        return False
    
    # Initialize pygame for testing
    pygame.init()
    
    # Create a mock kiosk instance
    kiosk = DoomBoxKiosk()
    
    # Replace video player with mock
    kiosk.video_player = MockVideoPlayer()
    kiosk.video_player.start()
    
    # Track video state changes
    video_states = []
    
    # Test initial state
    print(f"Initial video paused state: {kiosk.video_paused}")
    video_states.append(("initial", kiosk.video_paused))
    
    # Test game state change callbacks
    if hasattr(kiosk, 'game_launcher') and kiosk.game_launcher:
        # Simulate game starting
        kiosk._on_game_state_change("idle", "starting", "TestPlayer")
        video_states.append(("game_starting", kiosk.video_paused))
        
        # Simulate game running
        kiosk._on_game_state_change("starting", "running", "TestPlayer")
        video_states.append(("game_running", kiosk.video_paused))
        
        # Simulate game finished
        kiosk._on_game_state_change("running", "finished", "TestPlayer")
        video_states.append(("game_finished", kiosk.video_paused))
        
        # Simulate back to idle
        kiosk._on_game_state_change("finished", "idle", "TestPlayer")
        video_states.append(("back_to_idle", kiosk.video_paused))
    
    # Verify video state changes
    expected_states = [
        ("initial", False),
        ("game_starting", True),
        ("game_running", True),
        ("game_finished", False),
        ("back_to_idle", False)
    ]
    
    print("\nVideo state changes:")
    for i, (state_name, paused) in enumerate(video_states):
        expected_paused = expected_states[i][1] if i < len(expected_states) else False
        status = "✓" if paused == expected_paused else "✗"
        print(f"  {state_name}: paused={paused} {status}")
    
    # Test video frame retrieval
    print("\nTesting video frame retrieval:")
    
    # Should get frame when not paused
    kiosk.video_paused = False
    frame = kiosk.video_player.get_frame()
    print(f"Frame when not paused: {'✓' if frame else '✗'}")
    
    # Should still get frame when paused (pausing is handled in draw logic)
    kiosk.video_paused = True
    frame = kiosk.video_player.get_frame()
    print(f"Frame when paused: {'✓' if frame else '✗'}")
    
    # Cleanup
    kiosk.video_player.stop()
    pygame.quit()
    
    # Check results
    states_correct = all(
        actual[1] == expected[1] 
        for actual, expected in zip(video_states, expected_states)
    )
    
    return states_correct

def main():
    """Run integration test"""
    print("=" * 60)
    print("DoomBox Integration Test")
    print("=" * 60)
    
    try:
        success = test_integration()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ Integration test PASSED!")
            print("Game state management and video pause functionality is working correctly.")
            return 0
        else:
            print("❌ Integration test FAILED!")
            print("There are issues with the integration.")
            return 1
            
    except Exception as e:
        print(f"❌ Integration test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
