#!/bin/bash

# Script to run the crawler and build the web app
set -e  # Exit on error

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Running crawler..."
echo "=========================================="

# Run the crawler
cd "$PROJECT_ROOT/src_crawler"
uv run main.py

# Check if combined_data.json was created
CRAWLER_OUTPUT="$PROJECT_ROOT/src_crawler/data/raw/combined_data.json"
if [ ! -f "$CRAWLER_OUTPUT" ]; then
    echo "Error: combined_data.json not found at $CRAWLER_OUTPUT"
    exit 1
fi

echo ""
echo "=========================================="
echo "Copying combined_data.json to web app..."
echo "=========================================="

# Copy combined_data.json to web app public folder
WEB_PUBLIC="$PROJECT_ROOT/src_web/public/combined_data.json"
cp "$CRAWLER_OUTPUT" "$WEB_PUBLIC"
echo "✓ Copied combined_data.json to $WEB_PUBLIC"


echo "=========================================="
echo "Remove crawled data..."
echo "=========================================="

rm -rf "$PROJECT_ROOT/src_crawler/data"
echo "✓ Removed crawled data"

echo ""
echo "=========================================="
echo "Building web app..."
echo "=========================================="

# Build the web app
# cd "$PROJECT_ROOT/src_web"
# npm run build

# echo ""
# echo "=========================================="
# echo "✓ Build complete!"
# echo "=========================================="

