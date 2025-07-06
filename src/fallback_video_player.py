#!/usr/bin/env python3
"""
Fallback video player for systems without hardware acceleration
Uses pre-loaded frame caching for smooth playback
"""

import os
import time
import threading
import queue
import logging
import random
from pathlib import Path
from typing import Optional, List, Tuple, Dict

import pygame
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CachedVideoPlayer:
    """
    Video player that pre-loads and caches frames for smooth playback
    Designed for systems where hardware acceleration is not available
    """
    
    def __init__(self, video_dir: str, display_size: Tuple[int, int] = (1280, 960)):
        self.video_dir = Path(video_dir)
        self.display_size = display_size
        self.video_files = []
        self.current_video_index = 0
        
        # Frame cache settings
        self.cache_size = 90  # Cache 3 seconds at 30fps
        self.frame_cache = []
        self.cache_index = 0
        self.cache_lock = threading.Lock()
        
        # Performance settings
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps
        self.last_frame_time = 0
        
        # Background loading
        self.running = False
        self.load_thread = None
        self.load_queue = queue.Queue()
        
        # Video switching
        self.video_switch_timer = 0
        self.video_switch_interval = 600  # 20 seconds at 30fps
        
        self._load_video_list()
        
    def _load_video_list(self):
        """Load and shuffle video file list"""
        if not self.video_dir.exists():
            logger.error(f"Video directory does not exist: {self.video_dir}")
            return
            
        # Look for optimized videos first
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
    
    def _preload_video_frames(self, video_path: str, max_frames: int = None) -> List[pygame.Surface]:
        """
        Pre-load video frames into memory for smooth playback
        """
        frames = []
        cap = None
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return frames
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if max_frames:
                frame_count = min(frame_count, max_frames)
            
            logger.info(f"Pre-loading {frame_count} frames from {video_path.name}")
            
            for i in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert frame to pygame surface
                try:
                    # Resize if needed
                    if frame.shape[:2] != (self.display_size[1], self.display_size[0]):
                        frame = cv2.resize(frame, self.display_size, interpolation=cv2.INTER_LINEAR)
                    
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Create pygame surface
                    surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                    frames.append(surface)
                    
                    # Progress indicator
                    if i % 30 == 0:  # Every second
                        logger.debug(f"Loaded {i+1}/{frame_count} frames")
                        
                except Exception as e:
                    logger.error(f"Error converting frame {i}: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(frames)} frames")
            
        except Exception as e:
            logger.error(f"Error pre-loading video frames: {e}")
        finally:
            if cap:
                cap.release()
        
        return frames
    
    def _background_loader(self):
        """Background thread for loading video frames"""
        while self.running:
            try:
                # Wait for load request
                try:
                    video_path = self.load_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Load frames
                frames = self._preload_video_frames(video_path, self.cache_size)
                
                # Update cache
                with self.cache_lock:
                    self.frame_cache = frames
                    self.cache_index = 0
                
                logger.info(f"Background loaded {len(frames)} frames")
                
            except Exception as e:
                logger.error(f"Error in background loader: {e}")
    
    def _load_next_video(self):
        """Load the next video in the sequence"""
        if not self.video_files:
            return
            
        video_path = self.video_files[self.current_video_index]
        logger.info(f"Loading video: {video_path.name}")
        
        if self.running and self.load_thread:
            # Queue for background loading
            try:
                self.load_queue.put(video_path, timeout=0.1)
            except queue.Full:
                logger.warning("Load queue full, skipping video load")
        else:
            # Load synchronously
            frames = self._preload_video_frames(video_path, self.cache_size)
            with self.cache_lock:
                self.frame_cache = frames
                self.cache_index = 0
        
        # Move to next video
        self.current_video_index = (self.current_video_index + 1) % len(self.video_files)
        
        # Reshuffle when we've gone through all videos
        if self.current_video_index == 0:
            random.shuffle(self.video_files)
            logger.info("Reshuffled video playlist")
    
    def start(self):
        """Start the video player"""
        if not self.video_files:
            logger.warning("No videos to play")
            return False
            
        self.running = True
        
        # Start background loading thread
        self.load_thread = threading.Thread(target=self._background_loader, daemon=True)
        self.load_thread.start()
        
        # Load first video
        self._load_next_video()
        
        # Wait a bit for initial load
        time.sleep(0.5)
        
        logger.info("Cached video player started")
        return True
    
    def stop(self):
        """Stop the video player"""
        self.running = False
        
        if self.load_thread and self.load_thread.is_alive():
            self.load_thread.join(timeout=1.0)
        
        with self.cache_lock:
            self.frame_cache.clear()
            
        logger.info("Cached video player stopped")
    
    def get_frame(self) -> Optional[pygame.Surface]:
        """Get the current video frame"""
        current_time = time.time()
        
        # Check if it's time for next frame
        if current_time - self.last_frame_time < self.frame_time:
            # Return current frame (don't advance)
            with self.cache_lock:
                if self.frame_cache and self.cache_index < len(self.frame_cache):
                    return self.frame_cache[self.cache_index]
            return None
        
        # Time to advance frame
        self.last_frame_time = current_time
        
        with self.cache_lock:
            if not self.frame_cache:
                return None
            
            if self.cache_index >= len(self.frame_cache):
                # End of cached frames, load next video
                self.cache_index = 0
                self._load_next_video()
                return None
            
            frame = self.frame_cache[self.cache_index]
            self.cache_index += 1
            
            return frame
    
    def get_stats(self) -> Dict:
        """Get player statistics"""
        with self.cache_lock:
            cache_frames = len(self.frame_cache)
            cache_position = self.cache_index
        
        return {
            'video_count': len(self.video_files),
            'current_video': self.video_files[self.current_video_index].name if self.video_files else None,
            'cache_frames': cache_frames,
            'cache_position': cache_position,
            'cache_size_mb': cache_frames * self.display_size[0] * self.display_size[1] * 3 / (1024 * 1024),
            'target_fps': self.target_fps
        }


# Simple fallback for when all else fails
class SimpleVideoPlayer:
    """
    Ultra-simple video player that just cycles through a few cached frames
    """
    
    def __init__(self, video_dir: str, display_size: Tuple[int, int] = (1280, 960)):
        self.video_dir = Path(video_dir)
        self.display_size = display_size
        self.static_frames = []
        self.current_frame_index = 0
        self.last_frame_time = 0
        self.frame_time = 1.0 / 2  # Very slow, 2 FPS
        
        self._create_static_frames()
    
    def _create_static_frames(self):
        """Create a few static frames for minimal video effect"""
        try:
            # Try to load one frame from each video
            video_files = list(self.video_dir.glob('*.mp4'))[:5]  # Max 5 videos
            
            for video_file in video_files:
                cap = cv2.VideoCapture(str(video_file))
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        frame = cv2.resize(frame, self.display_size, interpolation=cv2.INTER_LINEAR)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                        self.static_frames.append(surface)
                cap.release()
            
            logger.info(f"Created {len(self.static_frames)} static frames")
            
        except Exception as e:
            logger.error(f"Error creating static frames: {e}")
            
        # Create a solid color frame as absolute fallback
        if not self.static_frames:
            surface = pygame.Surface(self.display_size)
            surface.fill((20, 10, 30))  # Dark purple
            self.static_frames = [surface]
    
    def start(self):
        return len(self.static_frames) > 0
    
    def stop(self):
        pass
    
    def get_frame(self) -> Optional[pygame.Surface]:
        """Get current frame (very slow cycling)"""
        current_time = time.time()
        
        if current_time - self.last_frame_time >= self.frame_time:
            self.last_frame_time = current_time
            self.current_frame_index = (self.current_frame_index + 1) % len(self.static_frames)
        
        return self.static_frames[self.current_frame_index]
    
    def get_stats(self) -> Dict:
        return {
            'video_count': len(self.static_frames),
            'current_video': 'static_frames',
            'player_type': 'simple_fallback'
        }


# Factory function to create appropriate video player
def create_video_player(video_dir: str, display_size: Tuple[int, int] = (1280, 960), prefer_hardware: bool = True):
    """
    Create the best available video player for the system
    """
    try:
        if prefer_hardware:
            # Try hardware-accelerated player first
            from hardware_video_player import HardwareVideoPlayer
            player = HardwareVideoPlayer(video_dir, display_size)
            if player.start():
                logger.info("Using hardware-accelerated video player")
                return player
            else:
                logger.warning("Hardware player failed to start")
        
        # Try cached player
        player = CachedVideoPlayer(video_dir, display_size)
        if player.start():
            logger.info("Using cached video player")
            return player
        else:
            logger.warning("Cached player failed to start")
            
    except Exception as e:
        logger.error(f"Error creating preferred video player: {e}")
    
    # Fall back to simple player
    logger.info("Using simple fallback video player")
    player = SimpleVideoPlayer(video_dir, display_size)
    player.start()
    return player
