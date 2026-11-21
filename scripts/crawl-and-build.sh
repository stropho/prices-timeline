#!/bin/bash

# Script to run the crawler and build the web app
set -e  # Exit on error

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CONFIG_FILE="$PROJECT_ROOT/src_crawler/config/target.config.yaml"

echo "=========================================="
echo "Loading targets from $CONFIG_FILE..."
echo "=========================================="

# Parse the YAML with pyyaml, run via uv so no project dependency is needed
# Each entry is emitted as "url|commonProductName" (empty when not set)
URLS=()
while read -r target; do
    URLS+=("$target")
done < <(uv run --directory "$PROJECT_ROOT/src_crawler" --with pyyaml python -c 'import sys, yaml; [print(item["url"] + "|" + str(item.get("commonProductName") or "")) for item in yaml.safe_load(open(sys.argv[1])) or []]' "$CONFIG_FILE")

if [ ${#URLS[@]} -eq 0 ]; then
    echo "Error: no URLs found in $CONFIG_FILE"
    exit 1
fi

BATCH_SIZE=5
BATCH_WAIT_SECONDS=$((45))
TOTAL_URLS=${#URLS[@]}
TOTAL_BATCHES=$(( (TOTAL_URLS + BATCH_SIZE - 1) / BATCH_SIZE ))

echo "✓ Loaded $TOTAL_URLS URL(s) in $TOTAL_BATCHES batch(es)"

echo "=========================================="
echo "Running crawler..."
echo "=========================================="

CRAWLER_OUTPUT_DIR="$PROJECT_ROOT/src_crawler/data/raw/json"
WEB_JSON_DIR="$PROJECT_ROOT/src_web/src/json"

copy_json_to_web_app() {
    # Check if crawler output folder was created
    if [ ! -d "$CRAWLER_OUTPUT_DIR" ]; then
        echo "Error: crawler output folder not found at $CRAWLER_OUTPUT_DIR"
        exit 1
    fi

    echo ""
    echo "=========================================="
    echo "Copying JSON folder to web app..."
    echo "=========================================="

    mkdir -p "$WEB_JSON_DIR"
    # rm -rf "$WEB_JSON_DIR"/*
    cp -R "$CRAWLER_OUTPUT_DIR"/. "$WEB_JSON_DIR"/
    echo "✓ Copied JSON files from $CRAWLER_OUTPUT_DIR to $WEB_JSON_DIR"
}

cd "$PROJECT_ROOT/src_crawler"
for (( start=0; start<TOTAL_URLS; start+=BATCH_SIZE )); do
    batch_num=$(( start / BATCH_SIZE + 1 ))
    batch=("${URLS[@]:start:BATCH_SIZE}")
    echo "Batch $batch_num/$TOTAL_BATCHES (${#batch[@]} URL(s))"
    uv run main.py "${batch[@]}"
    copy_json_to_web_app

    if (( start + BATCH_SIZE < TOTAL_URLS )); then
        echo "Waiting ${BATCH_WAIT_SECONDS}s before next batch..."
        sleep "$BATCH_WAIT_SECONDS"
    fi
done


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


