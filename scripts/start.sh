#!/bin/bash
# AI電話自動化 — ローカル起動スクリプト（Mac/Linux）
set -e

# Check/install uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

cd "$(dirname "$0")/.."
echo "Starting AI電話自動化..."
uv run phone-automation
