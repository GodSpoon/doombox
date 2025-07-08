#!/bin/bash
# Video optimization script for DoomBox kiosk
# Pre-processes videos for optimal playback performance on Radxa Zero

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo -e "  DoomBox Video Optimization"
echo -e "==========================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VID_DIR="$PROJECT_DIR/vid"
OPTIMIZED_DIR="$PROJECT_DIR/vid/optimized"

# Create optimized directory
mkdir -p "$OPTIMIZED_DIR"

# Target resolution for kiosk display
TARGET_WIDTH=1280
TARGET_HEIGHT=960
TARGET_FPS=30

echo -e "${YELLOW}Source directory: $VID_DIR${NC}"
echo -e "${YELLOW}Output directory: $OPTIMIZED_DIR${NC}"
echo -e "${YELLOW}Target resolution: ${TARGET_WIDTH}x${TARGET_HEIGHT}@${TARGET_FPS}fps${NC}"
echo ""

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg not found. Installing...${NC}"
    
    # Install ffmpeg with hardware acceleration support
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    else
        echo -e "${RED}Please install ffmpeg manually${NC}"
        exit 1
    fi
fi

# Function to optimize a single video
optimize_video() {
    local input_file="$1"
    local filename=$(basename "$input_file")
    local name="${filename%.*}"
    local output_file="$OPTIMIZED_DIR/${name}_optimized.mp4"
    
    echo -e "${BLUE}Processing: $filename${NC}"
    
    # Skip if already optimized
    if [[ -f "$output_file" ]]; then
        echo -e "${YELLOW}  Already optimized, skipping...${NC}"
        return 0
    fi
    
    # Get input video info
    local input_info=$(ffprobe -v quiet -print_format json -show_format -show_streams "$input_file" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}  Error reading video info, skipping...${NC}"
        return 1
    fi
    
    # Extract video dimensions and framerate
    local width=$(echo "$input_info" | jq -r '.streams[0].width // empty')
    local height=$(echo "$input_info" | jq -r '.streams[0].height // empty')
    local fps=$(echo "$input_info" | jq -r '.streams[0].r_frame_rate // empty' | bc -l 2>/dev/null || echo "30")
    
    echo -e "${YELLOW}  Input: ${width}x${height} @ ${fps}fps${NC}"
    
    # Optimize with hardware acceleration where available
    local hw_args=""
    
    # Try to detect hardware acceleration support
    if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
        hw_args="-c:v h264_v4l2m2m"
        echo -e "${GREEN}  Using hardware encoder: h264_v4l2m2m${NC}"
    elif ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_omx"; then
        hw_args="-c:v h264_omx"
        echo -e "${GREEN}  Using hardware encoder: h264_omx${NC}"
    else
        hw_args="-c:v libx264 -preset ultrafast"
        echo -e "${YELLOW}  Using software encoder (no hardware acceleration detected)${NC}"
    fi
    
    # Optimize video
    ffmpeg -y -i "$input_file" \
        -vf "scale=${TARGET_WIDTH}:${TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop=${TARGET_WIDTH}:${TARGET_HEIGHT}" \
        -r "$TARGET_FPS" \
        $hw_args \
        -crf 23 \
        -pix_fmt yuv420p \
        -movflags +faststart \
        -an \
        "$output_file" 2>/dev/null
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}  ✓ Optimized successfully${NC}"
        
        # Show file size comparison
        local input_size=$(stat -c%s "$input_file" 2>/dev/null || echo "0")
        local output_size=$(stat -c%s "$output_file" 2>/dev/null || echo "0")
        
        if [[ $input_size -gt 0 && $output_size -gt 0 ]]; then
            local reduction=$(( (input_size - output_size) * 100 / input_size ))
            echo -e "${BLUE}  Size reduction: ${reduction}%${NC}"
        fi
    else
        echo -e "${RED}  ✗ Optimization failed${NC}"
        rm -f "$output_file"
        return 1
    fi
    
    echo ""
}

# Process all video files
total_files=0
processed_files=0

echo -e "${YELLOW}Scanning for video files...${NC}"

# Use find to get all video files
while IFS= read -r -d '' file; do
    if [[ -f "$file" ]]; then
        ((total_files++))
        echo -e "${BLUE}Found: $(basename "$file")${NC}"
        
        if optimize_video "$file"; then
            ((processed_files++))
        fi
    fi
done < <(find "$VID_DIR" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.webm" -o -name "*.mkv" \) -print0)

if [[ $total_files -eq 0 ]]; then
    echo -e "${YELLOW}No video files found in $VID_DIR${NC}"
fi

echo -e "${GREEN}=========================================="
echo -e "  Optimization Complete!"
echo -e "==========================================${NC}"
echo -e "${BLUE}Total files: $total_files${NC}"
echo -e "${GREEN}Successfully processed: $processed_files${NC}"
echo -e "${YELLOW}Optimized videos saved to: $OPTIMIZED_DIR${NC}"
echo ""

# Create a symlink for easy access
if [[ $processed_files -gt 0 ]]; then
    echo -e "${YELLOW}Creating optimized video symlink...${NC}"
    ln -sfn "$OPTIMIZED_DIR" "$PROJECT_DIR/vid_optimized"
    echo -e "${GREEN}✓ Symlink created: $PROJECT_DIR/vid_optimized${NC}"
    echo ""
    echo -e "${BLUE}To use optimized videos, update your kiosk configuration to use:${NC}"
    echo -e "${YELLOW}  vid_optimized/ instead of vid/${NC}"
fi
