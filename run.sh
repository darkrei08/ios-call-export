#!/bin/bash
# ============================================================
# iOS Backup Explorer — One-Click Launcher (Linux / macOS)
# Double-click this file from your file manager, or run: ./run.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Auto-install uv if missing ---
if ! command -v uv &> /dev/null; then
    echo "📦 'uv' non trovato. Installazione automatica..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Reload PATH so 'uv' is available immediately
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# --- Sync dependencies (creates .venv if needed) ---
if [ -d ".venv" ]; then
    if ! uv run python -c "pass" >/dev/null 2>&1; then
        echo "📦 Rilevato ambiente virtuale corrotto (forse cloud-sync da Windows). Ricreazione..."
        rm -rf .venv
    fi
fi

if [ ! -d ".venv" ] || [ "pyproject.toml" -nt ".venv" ]; then
    echo "📦 Installazione dipendenze..."
    uv sync
fi

# --- Launch the GUI ---
echo "🚀 Avvio iOS Backup Explorer..."
uv run python gui.py
