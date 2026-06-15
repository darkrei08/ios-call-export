#!/bin/bash
# One-click launcher for iOS Backup Explorer
# Double-click this file or run: ./run.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if uv is available
if command -v uv &> /dev/null; then
    uv run python gui.py
elif [ -d ".venv" ]; then
    .venv/bin/python gui.py
else
    python3 gui.py
fi
