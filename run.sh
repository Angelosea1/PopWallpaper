#!/bin/bash
# PopWallpaper Launcher Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Setting up virtual environment..."
    
    # Check if python3-venv is installed
    if ! python3 -c "import venv" &> /dev/null; then
        echo "python3-venv is not installed."
        echo "Installing python3-venv..."
        sudo apt install -y python3-venv
    fi
    
    python3 -m venv "$SCRIPT_DIR/venv"
    "$SCRIPT_DIR/venv/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
fi

# Activate virtual environment and run
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    python3 "$SCRIPT_DIR/popwallpaper.py" "$@"
else
    # Fallback: try running directly
    cd "$SCRIPT_DIR"
    python3 popwallpaper.py "$@"
fi
