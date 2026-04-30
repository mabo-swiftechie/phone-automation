from __future__ import annotations
import os
from typing import Optional
import yaml
from app.paths import DATA_DIR

CONFIG_PATH = DATA_DIR / "config.yaml"

# Environment variable mapping: config key → env var name
ENV_MAP = {
    "openai_api_key": "OPENAI_API_KEY",
    "gmail_address": "GMAIL_ADDRESS",
    "gmail_app_password": "GMAIL_APP_PASSWORD",
    "retell_api_key": "RETELL_API_KEY",
    "retell_agent_id": "RETELL_AGENT_ID",
    "company_name": "COMPANY_NAME",
    "contact_person": "CONTACT_PERSON",
}

DEFAULTS = {
    "openai_api_key": "",
    "gmail_address": "",
    "gmail_app_password": "",
    "retell_api_key": "",
    "retell_agent_id": "",
    "company_name": "",
    "contact_person": "",
    "phone_number": "",
    "email_signature": "",
    "line_channel_access_token": "",
    "line_user_id": "",
    "base_url": "http://localhost:8000",
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = yaml.safe_load(f) or {}
    else:
        saved = {}
    merged = {**DEFAULTS, **saved}
    # Override with env vars (Replit Secrets / system env)
    for key, env_name in ENV_MAP.items():
        val = os.environ.get(env_name, "").strip()
        if val:
            merged[key] = val
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
