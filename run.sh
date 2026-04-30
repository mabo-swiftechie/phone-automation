#!/bin/bash
set -e

echo "=== Installing dependencies ==="
pip install . 2>&1 || { echo "ERROR: pip install failed"; exit 1; }

echo "=== Starting Streamlit ==="
streamlit run app/ui.py \
  --server.headless true \
  --server.port 8501 \
  --browser.gatherUsageStats false
