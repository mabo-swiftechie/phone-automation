from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

DEFAULTS = {
    "openai_api_key": "",
    "gmail_address": "",
    "gmail_app_password": "",
    "retell_api_key": "",
    "retell_agent_id": "",
    "company_name": "〇〇不動産",
    "contact_person": "担当者",
    "phone_number": "",
    "email_signature": "",
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = yaml.safe_load(f) or {}
    else:
        saved = {}
    merged = {**DEFAULTS, **saved}
    return merged


def save_config(config: dict):
    to_save = {k: v for k, v in config.items() if k in DEFAULTS}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(to_save, f, allow_unicode=True, default_flow_style=False)


def get(key: str) -> Optional[str]:
    cfg = load_config()
    return cfg.get(key)


def is_configured() -> bool:
    cfg = load_config()
    return bool(cfg.get("openai_api_key"))
