#!/usr/bin/env python3
"""
Test script for the optimized video playback system
"""

import sys
import os
import time
import pygame
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fallback_video_player import create_video_player

def test_video_player():
    """Test the video player system"""
    print("=== DoomBox Video Player Test ===")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1280, 960))
    pygame.display.set_caption("DoomBox Video Test")
    clock = pygame.time.Clock()
    
    # Create video player
    video_dir = Path(__file__).parent.parent / "vid"
    print(f"Looking for videos in: {video_dir}")
    
    if not video_dir.exists():
        print(f"Error: Video directory does not exist: {video_dir}")
        return False
    
    # Create video player
    player = create_video_player(str(video_dir), (1280, 960))
    
    if not player:
        print("Error: Failed to create video player")
        return False
    
    print("Video player created successfully!")
    print(f"Stats: {player.get_stats()}")
    
    # Test playback
    print("\nTesting video playback for 30 seconds...")
    print("Press ESC to exit early")
    
    start_time = time.time()
    frame_count = 0
    
    running = True
    while running and (time.time() - start_time) < 30:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_s:
                    print(f"Current stats: {player.get_stats()}")
        
        # Get and display frame
        frame = player.get_frame()
        if frame:
            screen.blit(frame, (0, 0))
        else:
            screen.fill((50, 25, 75))  # Dark purple background
        
        # Add some text overlay
        font = pygame.font.Font(None, 48)
        text = font.render(f"Frame: {frame_count}", True, (255, 255, 255))
        screen.blit(text, (50, 50))
        
        stats_text = font.render(f"FPS: {clock.get_fps():.1f}", True, (255, 255, 255))
        screen.blit(stats_text, (50, 100))
        
        pygame.display.flip()
        clock.tick(30)
        frame_count += 1
        
        # Print progress every 5 seconds
        if frame_count % 150 == 0:
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed
            print(f"Progress: {elapsed:.1f}s, {frame_count} frames, {actual_fps:.1f} FPS")
    
    # Stop player
    player.stop()
    pygame.quit()
    
    # Final stats
    total_time = time.time() - start_time
    final_fps = frame_count / total_time
    print(f"\nTest completed!")
    print(f"Total time: {total_time:.1f}s")
    print(f"Total frames: {frame_count}")
    print(f"Average FPS: {final_fps:.1f}")
    print(f"Final stats: {player.get_stats()}")
    
    return True

if __name__ == "__main__":
    success = test_video_player()
    sys.exit(0 if success else 1)
