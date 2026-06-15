#!/bin/bash
# ============================================================
# iOS Backup Explorer — macOS Finder Launcher
# Double-click this .command file from Finder to launch the app.
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- Auto-install uv if missing ---
if ! command -v uv &> /dev/null; then
    echo "📦 'uv' non trovato. Installazione automatica..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# --- Sync dependencies ---
if [ ! -d ".venv" ] || [ "pyproject.toml" -nt ".venv" ]; then
    echo "📦 Installazione dipendenze..."
    uv sync
fi

# --- Launch ---
echo "🚀 Avvio iOS Backup Explorer..."
uv run python gui.py
