#!/bin/bash
# Simple video optimization script for DoomBox

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
VID_DIR="/home/sam/SPOON_GIT/doombox/vid"
BACKUP_DIR="/home/sam/Videos/doom old"

# Settings
TARGET_WIDTH=1280
TARGET_HEIGHT=960
TARGET_FPS=30

echo -e "${GREEN}DoomBox Video Optimizer${NC}"
echo -e "Source: $VID_DIR"
echo -e "Backup: $BACKUP_DIR"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg not found${NC}"
    exit 1
fi

# Find videos
videos=($(find "$VID_DIR" -maxdepth 1 -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.webm" -o -name "*.mkv" -o -name "*.m4v" -o -name "*.flv"))
total=${#videos[@]}

if [[ $total -eq 0 ]]; then
    echo -e "${YELLOW}No videos found${NC}"
    exit 0
fi

echo -e "${GREEN}Found $total videos${NC}"
echo ""

# Process each video
count=0
failed=0

for video in "${videos[@]}"; do
    ((count++))
    filename=$(basename "$video")
    name="${filename%.*}"
    temp_output="/tmp/${name}_temp.mp4"
    final_output="$VID_DIR/${name}.mp4"
    
    echo -e "${BLUE}[$count/$total] Processing: $filename${NC}"
    
    # Optimize with NVENC
    if ffmpeg -y -hide_banner -loglevel error \
        -i "$video" \
        -vf "scale=$TARGET_WIDTH:$TARGET_HEIGHT:force_original_aspect_ratio=increase,crop=$TARGET_WIDTH:$TARGET_HEIGHT" \
        -c:v h264_nvenc \
        -preset fast \
        -cq 23 \
        -r $TARGET_FPS \
        -an \
        "$temp_output" 2>/dev/null; then
        
        # Move original to backup
        mv "$video" "$BACKUP_DIR/"
        
        # Move optimized to final location  
        mv "$temp_output" "$final_output"
        
        echo -e "${GREEN}  ✓ Optimized successfully${NC}"
    else
        echo -e "${RED}  ✗ Failed${NC}"
        rm -f "$temp_output"
        ((failed++))
    fi
done

echo ""
echo -e "${GREEN}Complete!${NC}"
echo -e "Processed: $count"
echo -e "Failed: $failed"
echo -e "Originals moved to: $BACKUP_DIR"

read -p "Press Enter to exit..."
