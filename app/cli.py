from __future__ import annotations
import sys
import subprocess
import time
import signal
from pathlib import Path
from app.paths import ensure_data_dir, DATA_DIR
from app.database import init_db


def main():
    ensure_data_dir()
    init_db()

    config_path = DATA_DIR / "config.yaml"
    if not config_path.exists():
        config_path.write_text("# AI電話自動化 設定ファイル\n", encoding="utf-8")

    # Start FastAPI (uvicorn)
    fastapi_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "warning",
    ]
    fastapi_proc = subprocess.Popen(fastapi_cmd)
    print("🚀 FastAPI started at http://localhost:8000")

    # Give uvicorn a moment to bind
    time.sleep(1)

    # Start Streamlit
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(Path(__file__).parent / "ui.py"),
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false",
    ]
    streamlit_proc = subprocess.Popen(streamlit_cmd)
    print("🖥️  Streamlit started at http://localhost:8501")

    def shutdown(signum, frame):
        print("\n👋 Shutting down...")
        streamlit_proc.terminate()
        fastapi_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        streamlit_proc.wait()
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
