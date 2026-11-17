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

# Check if crawler output folder was created
CRAWLER_OUTPUT_DIR="$PROJECT_ROOT/src_crawler/data/raw/json"
if [ ! -d "$CRAWLER_OUTPUT_DIR" ]; then
    echo "Error: crawler output folder not found at $CRAWLER_OUTPUT_DIR"
    exit 1
fi

echo ""
echo "=========================================="
echo "Copying JSON folder to web app..."
echo "=========================================="

# Copy all crawled JSON files to web app folder
WEB_JSON_DIR="$PROJECT_ROOT/src_web/src/json"
mkdir -p "$WEB_JSON_DIR"
rm -rf "$WEB_JSON_DIR"/*
cp -R "$CRAWLER_OUTPUT_DIR"/. "$WEB_JSON_DIR"/
echo "✓ Copied JSON files from $CRAWLER_OUTPUT_DIR to $WEB_JSON_DIR"


echo "=========================================="
echo "Remove crawled data..."
echo "=========================================="

rm -rf "$PROJECT_ROOT/src_crawler/data"
echo "✓ Removed crawled data"

echo ""
echo "=========================================="
echo "Review Changes and press any key to continue to push"
echo "=========================================="

read -n 1 -s -r -p ""

cd "$PROJECT_ROOT"
git add .
git commit -m "chore: Update crawled data"
git push


