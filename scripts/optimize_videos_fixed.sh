#!/bin/bash
# Enhanced Video optimization script for DoomBox - NVIDIA GPU version
# Fixed version with better error handling

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}=================================================="
echo -e "  DoomBox Video Optimization - Enhanced NVIDIA"
echo -e "==================================================${NC}"

# Configuration
VID_DIR="/home/sam/SPOON_GIT/doombox/vid"
BACKUP_DIR="/home/sam/Videos/doom old"
TEMP_OPTIMIZED_DIR="$VID_DIR/.optimized_temp"
PROGRESS_DIR="/tmp/video_optimize_$$"

# Target resolution for Radxa Zero SBC
TARGET_WIDTH=1280
TARGET_HEIGHT=960
TARGET_FPS=30

# Parallel processing settings
MAX_JOBS=$(($(nproc) / 2))
if [[ $MAX_JOBS -lt 1 ]]; then
    MAX_JOBS=1
fi

echo -e "${YELLOW}Source directory: $VID_DIR${NC}"
echo -e "${YELLOW}Backup directory: $BACKUP_DIR${NC}"
echo -e "${YELLOW}Target resolution: ${TARGET_WIDTH}x${TARGET_HEIGHT}@${TARGET_FPS}fps${NC}"
echo -e "${CYAN}GPU: NVIDIA RTX 2060 Super (NVENC)${NC}"
echo -e "${BLUE}Parallel jobs: $MAX_JOBS${NC}"
echo ""

# Create directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$TEMP_OPTIMIZED_DIR"
mkdir -p "$PROGRESS_DIR"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    rm -rf "$PROGRESS_DIR" 2>/dev/null || true
    rmdir "$TEMP_OPTIMIZED_DIR" 2>/dev/null || true
    exit
}
trap cleanup EXIT INT TERM

# Check dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg not found.${NC}"
    echo -e "${YELLOW}Install with: sudo pacman -S ffmpeg${NC}"
    exit 1
fi

# Check for NVENC support
NVENC_CHECK=$(ffmpeg -hide_banner -encoders 2>/dev/null | grep "h264_nvenc" || echo "")
if [[ -z "$NVENC_CHECK" ]]; then
    echo -e "${RED}Error: NVENC encoder not found in ffmpeg.${NC}"
    echo -e "${YELLOW}Make sure you have ffmpeg with NVIDIA support${NC}"
    exit 1
fi

# Check NVIDIA driver
if command -v nvidia-smi &> /dev/null; then
    echo -e "${CYAN}NVIDIA GPU Status:${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits | head -1
    echo ""
fi

# Progress tracking variables
declare -i TOTAL_FILES=0
declare -i COMPLETED_FILES=0
declare -i FAILED_FILES=0

# Safe function to count files
count_progress_files() {
    local pattern="$1"
    local count=0
    if [[ -d "$PROGRESS_DIR" ]]; then
        while IFS= read -r -d '' file; do
            ((count++))
        done < <(find "$PROGRESS_DIR" -name "$pattern" -print0 2>/dev/null)
    fi
    echo "$count"
}

# Function to update progress display
update_progress() {
    local completed=$(count_progress_files "*.completed")
    local failed=$(count_progress_files "*.failed")
    local active=$(count_progress_files "*.active")
    
    COMPLETED_FILES=$completed
    FAILED_FILES=$failed
    
    local progress_percent=0
    if [[ $TOTAL_FILES -gt 0 ]]; then
        progress_percent=$(( (completed + failed) * 100 / TOTAL_FILES ))
    fi
    
    # Create progress bar
    local bar_length=40
    local filled_length=$(( progress_percent * bar_length / 100 ))
    local bar=""
    
    for ((i=0; i<filled_length; i++)); do
        bar+="█"
    done
    for ((i=filled_length; i<bar_length; i++)); do
        bar+="░"
    done
    
    # Clear line and show progress
    printf "\r${CYAN}Progress: [${bar}] ${progress_percent}%% (${completed}/${TOTAL_FILES}) Active: ${active} Failed: ${failed}${NC}"
}

# Function to optimize a single video
optimize_video() {
    local input_file="$1"
    local job_id="$2"
    local filename=$(basename "$input_file")
    local name="${filename%.*}"
    local temp_output="$TEMP_OPTIMIZED_DIR/${name}_optimized.mp4"
    local final_output="$VID_DIR/${name}.mp4"
    
    # Mark job as active
    touch "$PROGRESS_DIR/${job_id}.active" || return 1
    
    local start_time=$(date +%s)
    local encode_result=1
    
    # Enhanced NVENC settings
    if ffmpeg -y -hide_banner -loglevel error \
        -hwaccel cuda -hwaccel_output_format cuda \
        -i "$input_file" \
        -vf "scale_cuda=${TARGET_WIDTH}:${TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop_cuda=${TARGET_WIDTH}:${TARGET_HEIGHT}" \
        -c:v h264_nvenc \
        -preset p1 \
        -tune hq \
        -rc vbr \
        -cq 20 \
        -b:v 0 \
        -maxrate 6M \
        -bufsize 12M \
        -r "$TARGET_FPS" \
        -pix_fmt yuv420p \
        -movflags +faststart \
        -an \
        "$temp_output" 2>/dev/null; then
        encode_result=0
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Remove active marker
    rm -f "$PROGRESS_DIR/${job_id}.active"
    
    if [[ $encode_result -eq 0 && -f "$temp_output" ]]; then
        # Get file sizes for comparison
        local input_size=$(stat -c%s "$input_file" 2>/dev/null || echo "0")
        local output_size=$(stat -c%s "$temp_output" 2>/dev/null || echo "0")
        
        if [[ $output_size -gt 0 ]]; then
            # Move original to backup directory
            mv "$input_file" "$BACKUP_DIR/"
            
            # Move optimized file to final location
            mv "$temp_output" "$final_output"
            
            # Calculate stats
            if [[ $input_size -gt 0 ]]; then
                local reduction=$(( (input_size - output_size) * 100 / input_size ))
                local input_mb=$((input_size / 1024 / 1024))
                local output_mb=$((output_size / 1024 / 1024))
                echo "SUCCESS: $filename (${duration}s, ${input_mb}MB→${output_mb}MB, -${reduction}%)" > "$PROGRESS_DIR/${job_id}.completed"
            else
                echo "SUCCESS: $filename (${duration}s)" > "$PROGRESS_DIR/${job_id}.completed"
            fi
            
            return 0
        fi
    fi
    
    echo "FAILED: $filename" > "$PROGRESS_DIR/${job_id}.failed"
    rm -f "$temp_output"
    return 1
}

# Scan for video files
echo -e "${YELLOW}Scanning for video files...${NC}"

video_files=()
while IFS= read -r -d '' file; do
    if [[ -f "$file" ]]; then
        video_files+=("$file")
    fi
done < <(find "$VID_DIR" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.webm" -o -name "*.mkv" -o -name "*.m4v" -o -name "*.flv" \) -print0)

TOTAL_FILES=${#video_files[@]}

if [[ $TOTAL_FILES -eq 0 ]]; then
    echo -e "${YELLOW}No video files found in $VID_DIR${NC}"
    exit 0
fi

echo -e "${GREEN}Found $TOTAL_FILES video files${NC}"
echo -e "${CYAN}Starting parallel optimization...${NC}"
echo ""

# Process all videos in parallel with job control
total_start_time=$(date +%s)
job_id=0

for file in "${video_files[@]}"; do
    # Wait for available slot
    while [[ $(count_progress_files "*.active") -ge $MAX_JOBS ]]; do
        update_progress
        sleep 0.5
    done
    
    # Start new job
    ((job_id++))
    optimize_video "$file" "$job_id" &
    
    # Brief pause to prevent overwhelming the GPU
    sleep 0.2
    update_progress
done

# Wait for all jobs to complete with live progress updates
echo -e "\n${MAGENTA}Processing videos...${NC}"
while [[ $(count_progress_files "*.active") -gt 0 ]]; do
    update_progress
    sleep 1
done

# Final progress update
update_progress
echo ""

# Wait for any remaining background processes
wait

# Calculate total time
total_end_time=$(date +%s)
total_duration=$((total_end_time - total_start_time))
total_minutes=$((total_duration / 60))
total_seconds=$((total_duration % 60))

echo ""
echo -e "${GREEN}=================================================="
echo -e "  Optimization Complete!"
echo -e "==================================================${NC}"
echo -e "${BLUE}Total files processed: $TOTAL_FILES${NC}"
echo -e "${GREEN}Successfully optimized: $COMPLETED_FILES${NC}"
if [[ $FAILED_FILES -gt 0 ]]; then
    echo -e "${RED}Failed: $FAILED_FILES${NC}"
fi
echo -e "${CYAN}Total time: ${total_minutes}m ${total_seconds}s${NC}"
echo -e "${YELLOW}Original videos moved to: $BACKUP_DIR${NC}"
echo ""

# Show individual results
if [[ $COMPLETED_FILES -gt 0 ]]; then
    echo -e "${GREEN}Successfully optimized files:${NC}"
    find "$PROGRESS_DIR" -name "*.completed" -exec cat {} \; 2>/dev/null | while read -r line; do
        echo -e "  ${GREEN}✓${NC} ${line#SUCCESS: }"
    done
    echo ""
fi

if [[ $FAILED_FILES -gt 0 ]]; then
    echo -e "${RED}Failed files:${NC}"
    find "$PROGRESS_DIR" -name "*.failed" -exec cat {} \; 2>/dev/null | while read -r line; do
        echo -e "  ${RED}✗${NC} ${line#FAILED: }"
    done
    echo ""
fi

# Show disk usage
if command -v du &> /dev/null; then
    local optimized_size=$(du -sh "$VID_DIR" 2>/dev/null | cut -f1 || echo "Unknown")
    local backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "Unknown")
    echo -e "${BLUE}Disk usage:${NC}"
    echo -e "  Optimized videos: $optimized_size"
    echo -e "  Backup originals: $backup_size"
    echo ""
fi

if [[ $COMPLETED_FILES -gt 0 ]]; then
    echo -e "${GREEN}🚀 Enhanced NVENC optimization completed!${NC}"
    if [[ $total_duration -gt 0 ]]; then
        local avg_speed=$(echo "scale=1; $COMPLETED_FILES * 60 / $total_duration" | bc 2>/dev/null || echo "N/A")
        echo -e "${CYAN}Average speed: ${avg_speed} videos/min (${MAX_JOBS} parallel jobs)${NC}"
    fi
    echo ""
    echo -e "${CYAN}Videos are now optimized for Radxa Zero SBC performance!${NC}"
    echo -e "${YELLOW}Ready to sync to Radxa Zero or commit to git${NC}"
fi

echo -e "${MAGENTA}Press any key to exit...${NC}"
read -n 1 -s
