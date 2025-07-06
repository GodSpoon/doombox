#!/usr/bin/env python3
"""
Hardware-accelerated video player for DoomBox kiosk
Optimized for ARM64 systems with GPU acceleration
"""

import os
import sys
import time
import threading
import queue
import logging
import random
from pathlib import Path
from typing import Optional, List, Tuple

import pygame
import subprocess
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


class HardwareVideoPlayer:
    """Hardware-accelerated video player optimized for ARM64 kiosk systems"""
    
    def __init__(self, video_dir: str, display_size: Tuple[int, int] = (1280, 960)):
        self.video_dir = Path(video_dir)
        self.display_size = display_size
        self.current_surface = None
        self.video_files = []
        self.current_video_index = 0
        
        # Performance settings
        self.frame_skip = 1  # Skip frames for better performance
        self.frame_buffer_size = 3  # Number of frames to buffer
        self.use_threading = True
        
        # Threading components
        self.frame_queue = queue.Queue(maxsize=self.frame_buffer_size)
        self.decode_thread = None
        self.running = False
        
        # Current video state
        self.current_video_cap = None
        self.video_fps = 30
        self.frame_time = 1.0 / self.video_fps
        self.last_frame_time = 0
        
        # Hardware acceleration detection
        self.hw_decode_available = self._detect_hardware_acceleration()
        
        self._load_video_list()
        
    def _detect_hardware_acceleration(self) -> bool:
        """Detect available hardware acceleration options"""
        try:
            # Check for V4L2 M2M decoder (common on ARM SBCs)
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-decoders'],
                capture_output=True, text=True, timeout=5
            )
            
            if 'h264_v4l2m2m' in result.stdout:
                logger.info("Hardware decoder detected: h264_v4l2m2m")
                return True
            elif 'h264_mmal' in result.stdout:
                logger.info("Hardware decoder detected: h264_mmal")
                return True
            elif 'h264_omx' in result.stdout:
                logger.info("Hardware decoder detected: h264_omx")
                return True
            else:
                logger.warning("No hardware video decoder detected, using software decoding")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not detect hardware acceleration: {e}")
            return False
    
    def _load_video_list(self):
        """Load and shuffle video file list"""
        if not self.video_dir.exists():
            logger.error(f"Video directory does not exist: {self.video_dir}")
            return
            
        # Look for optimized videos first, then fall back to originals
        optimized_dir = self.video_dir / 'optimized'
        if optimized_dir.exists():
            self.video_files = list(optimized_dir.glob('*_optimized.mp4'))
            logger.info(f"Found {len(self.video_files)} optimized videos")
        
        if not self.video_files:
            # Fall back to original videos
            patterns = ['*.mp4', '*.avi', '*.mov', '*.webm']
            for pattern in patterns:
                self.video_files.extend(self.video_dir.glob(pattern))
            logger.info(f"Found {len(self.video_files)} original videos")
        
        if self.video_files:
            random.shuffle(self.video_files)
            logger.info(f"Loaded {len(self.video_files)} video files")
        else:
            logger.warning("No video files found")
    
    def _create_hardware_video_capture(self, video_path: str) -> Optional[cv2.VideoCapture]:
        """Create video capture with hardware acceleration if available"""
        try:
            if self.hw_decode_available:
                # Try hardware-accelerated capture
                cap = cv2.VideoCapture(video_path, cv2.CAP_V4L2)
                if cap.isOpened():
                    logger.info(f"Using hardware-accelerated capture for {video_path}")
                    return cap
                else:
                    logger.warning("Hardware capture failed, falling back to software")
            
            # Fall back to software capture
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                logger.info(f"Using software capture for {video_path}")
                return cap
            else:
                logger.error(f"Failed to open video: {video_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating video capture: {e}")
            return None
    
    def _optimize_cv2_settings(self, cap: cv2.VideoCapture):
        """Optimize OpenCV capture settings for performance"""
        try:
            # Set buffer size to minimum to reduce latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to set hardware acceleration properties
            if self.hw_decode_available:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            
            # Get and log video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Video properties: {width}x{height} @ {fps:.1f}fps")
            
            # Update our FPS tracking
            if fps > 0:
                self.video_fps = fps
                self.frame_time = 1.0 / fps
            
        except Exception as e:
            logger.warning(f"Could not optimize capture settings: {e}")
    
    def _decode_thread_worker(self):
        """Background thread for video decoding"""
        while self.running:
            try:
                if not self.current_video_cap or not self.current_video_cap.isOpened():
                    time.sleep(0.1)
                    continue
                
                ret, frame = self.current_video_cap.read()
                
                if not ret:
                    # Video ended, load next video
                    self._load_next_video()
                    continue
                
                # Convert and resize frame efficiently
                surface = self._convert_frame_to_surface(frame)
                
                if surface:
                    # Try to add to queue, skip if full
                    try:
                        self.frame_queue.put(surface, timeout=0.001)
                    except queue.Full:
                        # Skip frame if queue is full
                        pass
                
            except Exception as e:
                logger.error(f"Error in decode thread: {e}")
                time.sleep(0.1)
    
    def _convert_frame_to_surface(self, frame) -> Optional[pygame.Surface]:
        """Efficiently convert OpenCV frame to pygame surface"""
        try:
            # Resize frame if needed (this should be pre-done for optimized videos)
            if frame.shape[:2] != (self.display_size[1], self.display_size[0]):
                frame = cv2.resize(frame, self.display_size, interpolation=cv2.INTER_LINEAR)
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create pygame surface
            surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            
            return surface
            
        except Exception as e:
            logger.error(f"Error converting frame: {e}")
            return None
    
    def _load_next_video(self):
        """Load the next video in the sequence"""
        if not self.video_files:
            return
            
        try:
            # Release current video
            if self.current_video_cap:
                self.current_video_cap.release()
            
            # Get next video
            video_path = str(self.video_files[self.current_video_index])
            self.current_video_cap = self._create_hardware_video_capture(video_path)
            
            if self.current_video_cap:
                self._optimize_cv2_settings(self.current_video_cap)
                logger.info(f"Loaded video: {self.video_files[self.current_video_index].name}")
            
            # Move to next video
            self.current_video_index = (self.current_video_index + 1) % len(self.video_files)
            
            # Reshuffle when we've gone through all videos
            if self.current_video_index == 0:
                random.shuffle(self.video_files)
                logger.info("Reshuffled video playlist")
                
        except Exception as e:
            logger.error(f"Error loading next video: {e}")
            self.current_video_cap = None
    
    def start(self):
        """Start the video player"""
        if not self.video_files:
            logger.warning("No videos to play")
            return False
            
        self.running = True
        
        # Load first video
        self._load_next_video()
        
        # Start decode thread if using threading
        if self.use_threading and self.current_video_cap:
            self.decode_thread = threading.Thread(target=self._decode_thread_worker, daemon=True)
            self.decode_thread.start()
            logger.info("Started background video decode thread")
            
        return True
    
    def stop(self):
        """Stop the video player"""
        self.running = False
        
        if self.decode_thread and self.decode_thread.is_alive():
            self.decode_thread.join(timeout=1.0)
            
        if self.current_video_cap:
            self.current_video_cap.release()
            
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
                
        logger.info("Video player stopped")
    
    def get_frame(self) -> Optional[pygame.Surface]:
        """Get the current video frame"""
        current_time = time.time()
        
        if self.use_threading:
            # Get frame from buffer queue
            try:
                surface = self.frame_queue.get_nowait()
                self.current_surface = surface
                self.last_frame_time = current_time
                return surface
            except queue.Empty:
                # Return last frame if queue is empty
                return self.current_surface
        else:
            # Synchronous frame reading
            if not self.current_video_cap or not self.current_video_cap.isOpened():
                return self.current_surface
            
            # Check if it's time for next frame
            if current_time - self.last_frame_time < self.frame_time:
                return self.current_surface
            
            ret, frame = self.current_video_cap.read()
            
            if not ret:
                self._load_next_video()
                return self.current_surface
            
            surface = self._convert_frame_to_surface(frame)
            if surface:
                self.current_surface = surface
                self.last_frame_time = current_time
                
            return self.current_surface
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        return {
            'video_count': len(self.video_files),
            'current_video': self.video_files[self.current_video_index].name if self.video_files else None,
            'hardware_acceleration': self.hw_decode_available,
            'threading_enabled': self.use_threading,
            'queue_size': self.frame_queue.qsize() if self.use_threading else 0,
            'fps': self.video_fps
        }


# Example usage and testing
if __name__ == "__main__":
    import pygame
    
    # Initialize pygame for testing
    pygame.init()
    screen = pygame.display.set_mode((1280, 960))
    pygame.display.set_caption("Hardware Video Player Test")
    clock = pygame.time.Clock()
    
    # Create video player
    video_dir = Path(__file__).parent.parent / "vid"
    player = HardwareVideoPlayer(str(video_dir))
    
    print("Starting video player...")
    if not player.start():
        print("Failed to start video player")
        sys.exit(1)
    
    print("Video player stats:", player.get_stats())
    
    # Main loop
    running = True
    frame_count = 0
    start_time = time.time()
    
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_s:
                        print("Stats:", player.get_stats())
            
            # Get and display video frame
            frame = player.get_frame()
            if frame:
                screen.blit(frame, (0, 0))
            else:
                screen.fill((0, 0, 0))
            
            pygame.display.flip()
            clock.tick(30)
            
            frame_count += 1
            if frame_count % 300 == 0:  # Every 10 seconds at 30fps
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed
                print(f"Actual FPS: {actual_fps:.1f}")
                
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        player.stop()
        pygame.quit()
