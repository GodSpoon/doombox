#!/bin/bash
# Setup script for video optimization dependencies

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Video Optimization Setup"
echo -e "==========================================${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}Running as root - good for system packages${NC}"
else
   echo -e "${YELLOW}Not running as root - may need sudo for some packages${NC}"
fi

# Update package list
echo -e "${BLUE}Updating package list...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get update
elif command -v yum &> /dev/null; then
    yum update -y
else
    echo -e "${YELLOW}Unknown package manager, skipping update${NC}"
fi

# Install FFmpeg with hardware acceleration
echo -e "${BLUE}Installing FFmpeg with hardware acceleration...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get install -y ffmpeg v4l-utils
    
    # Try to install hardware acceleration packages
    echo -e "${BLUE}Installing hardware acceleration packages...${NC}"
    
    # For Raspberry Pi / VideoCore
    if [[ -f /opt/vc/bin/vcgencmd ]]; then
        echo -e "${GREEN}Raspberry Pi detected${NC}"
        # GPU memory split might help
        echo -e "${YELLOW}Consider setting GPU memory split: raspi-config > Advanced > Memory Split > 128${NC}"
    fi
    
    # For general ARM systems
    if [[ $(uname -m) == "aarch64" || $(uname -m) == "armv7l" ]]; then
        echo -e "${GREEN}ARM system detected${NC}"
        # V4L2 support
        apt-get install -y v4l2loopback-dkms || echo -e "${YELLOW}v4l2loopback installation failed (may not be available)${NC}"
    fi
    
elif command -v yum &> /dev/null; then
    yum install -y ffmpeg v4l-utils
else
    echo -e "${RED}Could not install FFmpeg - please install manually${NC}"
fi

# Install jq for JSON parsing
echo -e "${BLUE}Installing jq for JSON parsing...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get install -y jq
elif command -v yum &> /dev/null; then
    yum install -y jq
else
    echo -e "${YELLOW}Could not install jq${NC}"
fi

# Install bc for calculations
echo -e "${BLUE}Installing bc for calculations...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get install -y bc
elif command -v yum &> /dev/null; then
    yum install -y bc
else
    echo -e "${YELLOW}Could not install bc${NC}"
fi

# Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
    pip3 install -r "$PROJECT_DIR/requirements.txt"
else
    echo -e "${YELLOW}requirements.txt not found, installing core dependencies...${NC}"
    pip3 install pygame qrcode[pil] numpy opencv-python pillow psutil
fi

# Test installations
echo -e "${BLUE}Testing installations...${NC}"

# Test FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓ FFmpeg installed${NC}"
    ffmpeg -version | head -1
else
    echo -e "${RED}✗ FFmpeg not found${NC}"
fi

# Test hardware acceleration
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_v4l2m2m\|h264_omx\|h264_mmal"; then
    echo -e "${GREEN}✓ Hardware acceleration available${NC}"
else
    echo -e "${YELLOW}⚠ No hardware acceleration detected${NC}"
fi

# Test Python modules
python3 -c "import pygame, cv2, numpy, PIL; print('✓ Python modules OK')" || echo -e "${RED}✗ Python module import failed${NC}"

# GPU memory check (if available)
if command -v vcgencmd &> /dev/null; then
    echo -e "${BLUE}GPU memory configuration:${NC}"
    vcgencmd get_mem arm && vcgencmd get_mem gpu
fi

echo -e "${GREEN}=========================================="
echo -e "  Setup Complete!"
echo -e "==========================================${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Test video optimization: ${BLUE}$PROJECT_DIR/scripts/test-video-optimization.sh${NC}"
echo -e "2. Optimize your videos: ${BLUE}$PROJECT_DIR/scripts/optimize-videos.sh${NC}"
echo -e "3. Test video playback: ${BLUE}python3 $PROJECT_DIR/scripts/test-video-player.py${NC}"
echo -e "4. Monitor performance: ${BLUE}python3 $PROJECT_DIR/scripts/performance-monitor.py${NC}"

echo -e "${GREEN}Your system is ready for optimized video playback!${NC}"
