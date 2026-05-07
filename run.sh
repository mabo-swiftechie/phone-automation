#!/bin/bash
set -e

export PHONE_AUTOMATION_DATA="${PHONE_AUTOMATION_DATA:-$HOME/.phone_automation}"
mkdir -p "$PHONE_AUTOMATION_DATA"

# ── Clean up existing processes on project ports ──
echo "=== Checking existing processes ==="
# Port 8501: Streamlit (project-specific, safe to kill)
PID=$(lsof -ti:8501 2>/dev/null || true)
if [ -n "$PID" ]; then
  echo "  Killing Streamlit on port 8501 (PID: $PID)"
  kill $PID 2>/dev/null || true
  sleep 1
fi
# Port 8000: only kill if it's our uvicorn process
PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PID" ]; then
  CMD=$(ps -p $PID -o command= 2>/dev/null || true)
  if echo "$CMD" | grep -q "uvicorn\|phone_automation"; then
    echo "  Killing uvicorn on port 8000 (PID: $PID)"
    kill $PID 2>/dev/null || true
    sleep 1
  else
    echo "  Port 8000 in use by unrelated process, skipping: $CMD"
  fi
fi

# ── Install dependencies ──
PIP_CMD="${PIP_CMD:-}"
if [ -n "$PIP_CMD" ]; then
  :
elif command -v pip3 &>/dev/null; then
  PIP_CMD=pip3
elif command -v pip &>/dev/null; then
  PIP_CMD=pip
else
  PIP_CMD="python3 -m pip"
fi

echo "=== Installing dependencies ==="
$PIP_CMD install . 2>&1 || { echo "ERROR: pip install failed"; exit 1; }

# ── Resolve streamlit command ──
STREAMLIT_CMD="${STREAMLIT_CMD:-}"
if [ -n "$STREAMLIT_CMD" ]; then
  :
elif command -v streamlit &>/dev/null; then
  STREAMLIT_CMD=streamlit
else
  STREAMLIT_CMD="python3 -m streamlit"
fi

echo "=== Starting Streamlit on http://localhost:8501 ==="
$STREAMLIT_CMD run app/ui.py \
  --server.headless true \
  --server.port 8501 \
  --browser.gatherUsageStats false
