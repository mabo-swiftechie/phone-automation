from __future__ import annotations
from pathlib import Path
import os


def get_data_dir() -> Path:
    """User data directory: ~/.phone_automation/ or PHONE_AUTOMATION_DATA env."""
    env = os.environ.get("PHONE_AUTOMATION_DATA")
    if env:
        return Path(env)
    return Path.home() / ".phone_automation"


DATA_DIR = get_data_dir()


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
