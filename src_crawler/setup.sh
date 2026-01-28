#!/usr/bin/env bash
# Setup script using uv

echo "Setting up prices-timeline project..."
echo "======================================"

# Install Python 3.12 using uv (lightweight, doesn't need disk space)
echo "Installing Python 3.12 via uv..."
$HOME/.local/bin/uv python install 3.12 2>/dev/null || echo "Python 3.12 already available"

# Pin to Python 3.12
echo "Pinning Python version..."
$HOME/.local/bin/uv python pin 3.12

# Sync dependencies
echo "Installing dependencies..."
$HOME/.local/bin/uv sync

# Setup crawl4ai
echo "Setting up crawl4ai (downloading browser)..."
$HOME/.local/bin/uv run crawl4ai-setup

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the crawler:"
echo "  cd src_crawler && uv run main.py"
echo ""
echo "Or activate the environment:"
echo "  source .venv/bin/activate"
echo "  cd src_crawler && python main.py"
