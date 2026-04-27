from __future__ import annotations
from functools import lru_cache
from typing import Optional
from app.config_manager import load_config


class Settings:
    """Unified settings backed by config.yaml (zero external dependencies)."""

    @property
    def twilio_account_sid(self) -> str:
        return load_config().get("twilio_account_sid", "")

    @property
    def twilio_auth_token(self) -> str:
        return load_config().get("twilio_auth_token", "")

    @property
    def twilio_phone_number(self) -> str:
        return load_config().get("twilio_phone_number", "")

    @property
    def retell_api_key(self) -> str:
        return load_config().get("retell_api_key", "")

    @property
    def retell_agent_id(self) -> str:
        return load_config().get("retell_agent_id", "")

    @property
    def line_channel_access_token(self) -> str:
        return load_config().get("line_channel_access_token", "")

    @property
    def line_user_id(self) -> str:
        return load_config().get("line_user_id", "")

    @property
    def base_url(self) -> str:
        return load_config().get("base_url", "http://localhost:8000")

    @property
    def debug(self) -> bool:
        return True


@lru_cache
def get_settings() -> Settings:
    return Settings()
