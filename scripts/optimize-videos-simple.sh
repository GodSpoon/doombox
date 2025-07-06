#!/bin/bash
# Simplified video optimization script for DoomBox

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}DoomBox Video Optimization${NC}"
echo ""

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VID_DIR="$PROJECT_DIR/vid"
OPTIMIZED_DIR="$PROJECT_DIR/vid/optimized"

echo "Source: $VID_DIR"
echo "Output: $OPTIMIZED_DIR"

# Create output directory
mkdir -p "$OPTIMIZED_DIR"

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg not found${NC}"
    exit 1
fi

# Find video files
echo -e "${YELLOW}Finding video files...${NC}"
VIDEO_FILES=($(find "$VID_DIR" -maxdepth 1 -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.webm" | head -3))

if [[ ${#VIDEO_FILES[@]} -eq 0 ]]; then
    echo -e "${RED}No video files found${NC}"
    exit 1
fi

echo -e "${GREEN}Found ${#VIDEO_FILES[@]} video files${NC}"

# Process first few videos as test
for video in "${VIDEO_FILES[@]}"; do
    filename=$(basename "$video")
    name="${filename%.*}"
    output="$OPTIMIZED_DIR/${name}_optimized.mp4"
    
    echo -e "${BLUE}Processing: $filename${NC}"
    
    if [[ -f "$output" ]]; then
        echo -e "${YELLOW}Already exists, skipping${NC}"
        continue
    fi
    
    # Simple optimization - resize and reduce quality
    ffmpeg -y -i "$video" \
        -vf "scale=1280:960:force_original_aspect_ratio=increase,crop=1280:960" \
        -c:v libx264 -crf 25 -preset fast \
        -r 30 -pix_fmt yuv420p \
        -an \
        "$output" 2>/dev/null
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ Successfully optimized${NC}"
    else
        echo -e "${RED}✗ Failed to optimize${NC}"
    fi
    
    echo ""
done

echo -e "${GREEN}Optimization complete!${NC}"
echo "Optimized videos are in: $OPTIMIZED_DIR"
