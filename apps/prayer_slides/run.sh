#!/bin/bash

echo "🙏 Prayer Slides Generator Setup"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv 2>/dev/null || {
        echo "❌ Virtual environment creation failed."
        echo "Please install python3-venv: sudo apt install python3-venv"
        echo "Or use pipx: pipx install streamlit youtube-transcript-api validators"
        exit 1
    }
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the app
echo "Starting Prayer Slides Generator..."
echo "Opening browser at http://localhost:8501"
streamlit run app.py