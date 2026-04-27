from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from app.paths import ensure_data_dir, DATA_DIR


def main():
    ensure_data_dir()

    config_path = DATA_DIR / "config.yaml"
    if not config_path.exists():
        config_path.write_text("# AI\u96fb\u8a71\u81ea\u52d5\u5316 \u8a2d\u5b9a\u30d5\u30a1\u30a4\u30eb\n", encoding="utf-8")

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(Path(__file__).parent / "ui.py"),
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false",
    ])


if __name__ == "__main__":
    main()
