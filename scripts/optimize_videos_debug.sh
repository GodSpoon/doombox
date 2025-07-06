#!/bin/bash
# Debug version to find the issue

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}Debug: Starting script${NC}"

# Configuration
VID_DIR="/home/sam/SPOON_GIT/doombox/vid"
BACKUP_DIR="/home/sam/Videos/doom old"
TEMP_OPTIMIZED_DIR="$VID_DIR/.optimized_temp"
PROGRESS_DIR="/tmp/video_optimize_$$"

echo -e "${GREEN}Debug: Variables set${NC}"

# Target resolution for Radxa Zero SBC
TARGET_WIDTH=1280
TARGET_HEIGHT=960
TARGET_FPS=30

# Parallel processing settings
MAX_JOBS=$(($(nproc) / 2))
if [[ $MAX_JOBS -lt 1 ]]; then
    MAX_JOBS=1
fi

echo -e "${GREEN}Debug: Max jobs = $MAX_JOBS${NC}"

# Create directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$TEMP_OPTIMIZED_DIR"
mkdir -p "$PROGRESS_DIR"

echo -e "${GREEN}Debug: Directories created${NC}"
echo -e "${GREEN}Progress dir: $PROGRESS_DIR${NC}"

# Progress tracking variables
TOTAL_FILES=0
COMPLETED_FILES=0
FAILED_FILES=0
ACTIVE_JOBS=0

echo -e "${GREEN}Debug: Variables initialized${NC}"

# Simple progress function for debugging
update_progress() {
    echo -e "${BLUE}Debug: In update_progress${NC}"
    
    local completed=0
    local failed=0
    local active=0
    
    if [[ -d "$PROGRESS_DIR" ]]; then
        completed=$(find "$PROGRESS_DIR" -name "*.completed" 2>/dev/null | wc -l || echo "0")
        failed=$(find "$PROGRESS_DIR" -name "*.failed" 2>/dev/null | wc -l || echo "0")
        active=$(find "$PROGRESS_DIR" -name "*.active" 2>/dev/null | wc -l || echo "0")
    fi
    
    echo -e "${CYAN}Progress: $completed completed, $failed failed, $active active${NC}"
}

echo -e "${GREEN}Debug: update_progress function defined${NC}"

# Test update_progress
echo -e "${GREEN}Debug: Testing update_progress${NC}"
update_progress

# Scan for video files
echo -e "${YELLOW}Scanning for video files...${NC}"

video_files=()
while IFS= read -r -d '' file; do
    if [[ -f "$file" ]]; then
        video_files+=("$file")
    fi
done < <(find "$VID_DIR" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.webm" -o -name "*.mkv" -o -name "*.m4v" -o -name "*.flv" \) -print0)

TOTAL_FILES=${#video_files[@]}
echo -e "${GREEN}Found $TOTAL_FILES video files${NC}"

if [[ $TOTAL_FILES -eq 0 ]]; then
    echo -e "${YELLOW}No video files found${NC}"
    exit 0
fi

echo -e "${GREEN}Debug: Starting processing loop${NC}"

# Test the loop structure
job_id=0
for file in "${video_files[@]}"; do
    echo -e "${BLUE}Debug: Processing file: $(basename "$file")${NC}"
    
    # Test job control
    echo -e "${BLUE}Debug: Checking active jobs${NC}"
    active_count=$(find "$PROGRESS_DIR" -name "*.active" 2>/dev/null | wc -l || echo "0")
    echo -e "${BLUE}Debug: Active jobs: $active_count, Max: $MAX_JOBS${NC}"
    
    if [[ $active_count -ge $MAX_JOBS ]]; then
        echo -e "${YELLOW}Debug: Would wait for slot${NC}"
        break  # Exit after first iteration for debugging
    fi
    
    ((job_id++))
    echo -e "${BLUE}Debug: Job ID: $job_id${NC}"
    
    # Don't actually start the job, just test the logic
    echo -e "${GREEN}Debug: Would start job for $(basename "$file")${NC}"
    
    update_progress
    
    # Only process first file for debugging
    break
done

echo -e "${GREEN}Debug: Loop completed successfully${NC}"
echo -e "${MAGENTA}Debug script completed - no actual processing done${NC}"

# Cleanup
rm -rf "$PROGRESS_DIR"
