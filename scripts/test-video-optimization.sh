#!/bin/bash
# Quick test script for video optimization on DoomBox

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Video Optimization Test"
echo -e "==========================================${NC}"

echo -e "${YELLOW}Project directory: $PROJECT_DIR${NC}"
echo ""

# Check system information
echo -e "${BLUE}=== System Information ===${NC}"
echo -e "CPU: $(nproc) cores"
echo -e "Memory: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo -e "Architecture: $(uname -m)"

# Check for hardware acceleration
echo -e "${BLUE}=== Hardware Acceleration Check ===${NC}"
if command -v vcgencmd &> /dev/null; then
    echo -e "${GREEN}✓ VideoCore tools available${NC}"
    vcgencmd get_mem gpu 2>/dev/null || echo -e "${YELLOW}Could not get GPU memory${NC}"
else
    echo -e "${YELLOW}VideoCore tools not available${NC}"
fi

if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓ FFmpeg available${NC}"
    
    # Check for hardware encoders
    if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
        echo -e "${GREEN}✓ Hardware encoder: h264_v4l2m2m${NC}"
    elif ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_omx"; then
        echo -e "${GREEN}✓ Hardware encoder: h264_omx${NC}"
    elif ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_mmal"; then
        echo -e "${GREEN}✓ Hardware encoder: h264_mmal${NC}"
    else
        echo -e "${YELLOW}⚠ No hardware encoders detected${NC}"
    fi
    
    # Check for hardware decoders
    if ffmpeg -hide_banner -decoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
        echo -e "${GREEN}✓ Hardware decoder: h264_v4l2m2m${NC}"
    elif ffmpeg -hide_banner -decoders 2>/dev/null | grep -q "h264_omx"; then
        echo -e "${GREEN}✓ Hardware decoder: h264_omx${NC}"
    elif ffmpeg -hide_banner -decoders 2>/dev/null | grep -q "h264_mmal"; then
        echo -e "${GREEN}✓ Hardware decoder: h264_mmal${NC}"
    else
        echo -e "${YELLOW}⚠ No hardware decoders detected${NC}"
    fi
else
    echo -e "${RED}✗ FFmpeg not available${NC}"
fi

# Check video files
echo -e "${BLUE}=== Video Files ===${NC}"
VID_DIR="$PROJECT_DIR/vid"
if [[ -d "$VID_DIR" ]]; then
    VIDEO_COUNT=$(find "$VID_DIR" -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.webm" | wc -l)
    echo -e "${GREEN}✓ Video directory exists${NC}"
    echo -e "Found $VIDEO_COUNT video files"
    
    # Show a sample video info
    SAMPLE_VIDEO=$(find "$VID_DIR" -name "*.mp4" | head -1)
    if [[ -n "$SAMPLE_VIDEO" ]]; then
        echo -e "${YELLOW}Sample video info:${NC}"
        if command -v ffprobe &> /dev/null; then
            ffprobe -v quiet -print_format json -show_format -show_streams "$SAMPLE_VIDEO" 2>/dev/null | jq -r '.streams[0] | "Resolution: \(.width)x\(.height), FPS: \(.r_frame_rate), Codec: \(.codec_name)"' 2>/dev/null || echo "Could not parse video info"
        else
            echo "ffprobe not available"
        fi
    fi
else
    echo -e "${RED}✗ Video directory not found${NC}"
fi

# Check for optimized videos
OPTIMIZED_DIR="$VID_DIR/optimized"
if [[ -d "$OPTIMIZED_DIR" ]]; then
    OPTIMIZED_COUNT=$(find "$OPTIMIZED_DIR" -name "*_optimized.mp4" | wc -l)
    echo -e "${GREEN}✓ Optimized video directory exists${NC}"
    echo -e "Found $OPTIMIZED_COUNT optimized videos"
else
    echo -e "${YELLOW}⚠ No optimized videos found${NC}"
    echo -e "Run: ${BLUE}$PROJECT_DIR/scripts/optimize-videos.sh${NC}"
fi

# Test performance monitoring
echo -e "${BLUE}=== Performance Test ===${NC}"
echo -e "${YELLOW}Running 10-second performance test...${NC}"

if [[ -f "$PROJECT_DIR/scripts/performance-monitor.py" ]]; then
    cd "$PROJECT_DIR"
    python3 scripts/performance-monitor.py --duration 10 --interval 2
else
    echo -e "${RED}Performance monitor script not found${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo -e "  Test Complete!"
echo -e "==========================================${NC}"

# Recommendations
echo -e "${BLUE}=== Recommendations ===${NC}"

if [[ $VIDEO_COUNT -gt 0 && ! -d "$OPTIMIZED_DIR" ]]; then
    echo -e "${YELLOW}1. Optimize videos for better performance:${NC}"
    echo -e "   cd $PROJECT_DIR && ./scripts/optimize-videos.sh"
fi

if ! ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_v4l2m2m\|h264_omx\|h264_mmal"; then
    echo -e "${YELLOW}2. Consider installing hardware acceleration:${NC}"
    echo -e "   sudo apt-get install v4l2loopback-dkms v4l-utils"
fi

echo -e "${YELLOW}3. Monitor performance during kiosk operation:${NC}"
echo -e "   cd $PROJECT_DIR && python3 scripts/performance-monitor.py"

echo -e "${YELLOW}4. Test the optimized kiosk:${NC}"
echo -e "   cd $PROJECT_DIR && ./start-kiosk.sh"
