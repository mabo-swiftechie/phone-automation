from __future__ import annotations
import sys
import threading
import time
from pathlib import Path

import uvicorn


def _start_fastapi():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning",
    )


def main():
    from app.paths import ensure_data_dir, DATA_DIR
    from app.database import init_db

    ensure_data_dir()
    init_db()

    config_path = DATA_DIR / "config.yaml"
    if not config_path.exists():
        config_path.write_text("# AI電話自動化 設定ファイル\n", encoding="utf-8")

    # FastAPI in background thread
    api_thread = threading.Thread(target=_start_fastapi, daemon=True)
    api_thread.start()
    print("🚀 FastAPI started at http://localhost:8000")
    time.sleep(1)

    # Streamlit as main process
    import subprocess
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(Path(__file__).parent / "ui.py"),
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false",
    ]
    print("🖥️  Streamlit started at http://localhost:8501")

    try:
        subprocess.run(streamlit_cmd)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


if __name__ == "__main__":
    main()
