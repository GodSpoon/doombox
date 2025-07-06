#!/bin/bash
# Ultra-simple video optimizer

VID_DIR="/home/sam/SPOON_GIT/doombox/vid"
BACKUP_DIR="/home/sam/Videos/doom old"

echo "DoomBox Video Optimizer"
echo "Source: $VID_DIR"
echo "Backup: $BACKUP_DIR"

mkdir -p "$BACKUP_DIR"

cd "$VID_DIR"
count=0
total=$(ls -1 *.mp4 *.avi *.mov *.webm *.mkv *.m4v *.flv 2>/dev/null | wc -l)

echo "Found $total videos"

for video in *.mp4 *.avi *.mov *.webm *.mkv *.m4v *.flv; do
    [[ ! -f "$video" ]] && continue
    
    count=$((count + 1))
    name="${video%.*}"
    
    echo "[$count/$total] $video"
    
    ffmpeg -y -i "$video" \
        -vf "scale=1280:960:force_original_aspect_ratio=increase,crop=1280:960" \
        -c:v h264_nvenc \
        -preset fast \
        -cq 23 \
        -r 30 \
        -an \
        "/tmp/${name}_opt.mp4" >/dev/null 2>&1 && {
        
        mv "$video" "$BACKUP_DIR/"
        mv "/tmp/${name}_opt.mp4" "${name}.mp4"
        echo "  ✓ Done"
    } || {
        echo "  ✗ Failed"
        rm -f "/tmp/${name}_opt.mp4"
    }
done

echo "Complete! Originals in: $BACKUP_DIR"
echo "Press Enter..."
read
