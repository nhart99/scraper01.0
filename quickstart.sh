#!/bin/bash
# Quick start script for RFP scraper

echo "========================================="
echo "  Utility RFP Scraper - Quick Start"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p output logs config

# Run the scraper with a test utility
echo ""
echo "========================================="
echo "  Testing with Pacific Gas & Electric"
echo "========================================="
echo ""

python src/main.py --utility pge --print-only

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "To run a full scrape of all utilities:"
echo "  python src/main.py"
echo ""
echo "To scrape a specific utility:"
echo "  python src/main.py --utility <utility_id>"
echo ""
echo "For more options:"
echo "  python src/main.py --help"
echo ""
