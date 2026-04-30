#!/bin/bash
set -e

export PHONE_AUTOMATION_DATA="${PHONE_AUTOMATION_DATA:-$HOME/.phone_automation}"
mkdir -p "$PHONE_AUTOMATION_DATA"

echo "=== Installing dependencies ==="
pip install . 2>&1 || { echo "ERROR: pip install failed"; exit 1; }

echo "=== Starting Streamlit ==="
streamlit run app/ui.py \
  --server.headless true \
  --server.port 8501 \
  --browser.gatherUsageStats false
