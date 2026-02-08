#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

echo "Starting pyLapse Web UI..."
python "$SCRIPT_DIR/web_ui.py" "$@"
