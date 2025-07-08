#!/bin/bash
# Show DoomBox directory structure

echo "📁 DoomBox Project Structure (Cleaned & Organized)"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

echo "📂 Root Directory:"
ls -1 *.sh *.md *.py Makefile 2>/dev/null | sed 's/^/  /'
echo ""

echo "📂 Main Directories:"
for dir in src scripts tests tools config; do
    if [ -d "$dir" ]; then
        echo "  $dir/"
        ls -1 "$dir" | sed 's/^/    /'
        echo ""
    fi
done

echo "📂 Asset Directories:"
for dir in fonts icons vid web; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -type f | wc -l)
        echo "  $dir/ ($count files)"
    fi
done

echo ""
echo "📊 File Summary:"
echo "  Python files: $(find . -name "*.py" -not -path "./venv/*" | wc -l)"
echo "  Shell scripts: $(find . -name "*.sh" | wc -l)"
echo "  Test files: $(find tests -name "*.py" 2>/dev/null | wc -l)"
echo "  Script utilities: $(find scripts -name "*" -type f 2>/dev/null | wc -l)"
echo ""

echo "✅ Project reorganization complete!"
echo "   - Tests moved to tests/ directory"
echo "   - Scripts organized by function"
echo "   - Tools consolidated in tools/"
echo "   - Duplicate files removed"
echo "   - Archive files moved to archives/"
