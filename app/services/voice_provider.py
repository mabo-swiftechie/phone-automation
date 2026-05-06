from __future__ import annotations

"""
Voice Provider abstraction layer.

Supports multiple tiers and providers through a unified interface.
Tier 1 (Free):  MockProvider or RetellProvider (Web Call only)
Tier 2 ($20):   RetellProvider with budget agent
Tier 3 ($100):  RetellProvider with Flow agent, or BlandProvider
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

import httpx

from app.config_manager import load_config
from app.services.template_manager import get_prompt_for_property


@dataclass
class CallResult:
    call_id: str
    status: str
    agent_mode: str = "default"


@dataclass
class WebCallResult:
    call_id: str
    access_token: str


@dataclass
class CallStatus:
    call_id: str
    status: str
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None


@dataclass
class WebhookResult:
    call_id: str
    call_status: str
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    vacancy_status: Optional[str] = None
    foreigner_accepted: Optional[bool] = None
    chinese_accepted: Optional[bool] = None
    special_conditions: Optional[str] = None


class VoiceProvider(ABC):
    """Abstract interface for voice call providers."""

    @abstractmethod
    def create_call(
        self,
        phone_number: str,
        property_name: str,
        property_id: str,
        mode: str = "default",
    ) -> CallResult:
        """Initiate a phone call. mode: "default" | "budget" | "flow" """

    @abstractmethod
    def create_web_call(
        self,
        property_name: str,
        property_id: str,
    ) -> WebCallResult:
        """Create a browser-based web call."""

    @abstractmethod
    def get_call_status(self, call_id: str) -> CallStatus:
        """Retrieve current call status."""

    @abstractmethod
    def parse_webhook(self, payload: dict) -> WebhookResult:
        """Parse a webhook payload into a unified result."""

    @property
    @abstractmethod
    def supports_batch(self) -> bool:
        """Whether batch calling is supported."""

    @property
    @abstractmethod
    def supports_phone_call(self) -> bool:
        """Whether real phone calls are supported."""

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""
        return self.__class__.__name__


class RetellProvider(VoiceProvider):
    """Retell AI provider (all tiers)."""

    _BASE_URL = "https://api.retellai.com/v2"

    def __init__(self, config: dict):
        self.api_key = config["retell_api_key"]
        self.agent_id = config["retell_agent_id"]
        self.budget_agent_id = config.get("retell_agent_id_budget") or ""
        self.flow_agent_id = config.get("retell_agent_id_flow") or ""

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _select_agent(self, mode: str) -> str:
        if mode == "budget" and self.budget_agent_id:
            return self.budget_agent_id
        if mode == "flow" and self.flow_agent_id:
            return self.flow_agent_id
        return self.agent_id

    @staticmethod
    def _to_e164(number: str) -> str:
        n = number.replace("-", "").replace(" ", "")
        if n.startswith("0"):
            n = "+81" + n[1:]
        elif not n.startswith("+"):
            n = "+" + n
        return n

    def create_call(
        self,
        phone_number: str,
        property_name: str,
        property_id: str,
        mode: str = "default",
    ) -> CallResult:
        agent_id = self._select_agent(mode)
        prompt = get_prompt_for_property(property_id)

        payload = {
            "agent_id": agent_id,
            "to": self._to_e164(phone_number),
            "metadata": {
                "property_id": property_id,
                "property_name": property_name,
            },
            "retell_llm_dynamic_variables": {
                "property_name": property_name,
                "conversation_template": prompt,
            },
        }

        with httpx.Client() as client:
            resp = client.post(
                f"{self._BASE_URL}/create-phone-call",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return CallResult(
            call_id=data.get("call_id", ""),
            status="initiated",
            agent_mode=mode,
        )

    def create_web_call(
        self,
        property_name: str,
        property_id: str,
    ) -> WebCallResult:
        prompt = get_prompt_for_property(property_id)

        payload = {
            "agent_id": self.agent_id,
            "metadata": {
                "property_id": property_id,
                "property_name": property_name,
            },
            "retell_llm_dynamic_variables": {
                "property_name": property_name,
                "conversation_template": prompt,
            },
        }

        with httpx.Client() as client:
            resp = client.post(
                f"{self._BASE_URL}/create-web-call",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return WebCallResult(
            call_id=data.get("call_id", ""),
            access_token=data.get("access_token", ""),
        )

    def get_call_status(self, call_id: str) -> CallStatus:
        with httpx.Client() as client:
            resp = client.get(
                f"{self._BASE_URL}/get-call/{call_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return CallStatus(
            call_id=data.get("call_id", call_id),
            status=data.get("call_status", "unknown"),
            duration_seconds=data.get("duration_seconds"),
            transcript=data.get("transcript"),
            recording_url=data.get("recording_url"),
        )

    def parse_webhook(self, payload: dict) -> WebhookResult:
        call_id = payload.get("call_id", "")
        call_status = payload.get("call_status", "unknown")
        analysis = payload.get("call_analysis") or {}
        structured = analysis.get("call_summary") or analysis.get("custom_analysis_data", {})

        vacancy = None
        foreigner = None
        chinese = None
        conditions = None
        if isinstance(structured, dict):
            vacancy = structured.get("vacancy_status")
            foreigner = structured.get("foreigner_accepted")
            chinese = structured.get("chinese_accepted")
            conditions = structured.get("special_conditions")

        def _to_bool(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.lower() in ("true", "yes", "1", "可", "可能")
            return None

        return WebhookResult(
            call_id=call_id,
            call_status=call_status,
            duration_seconds=payload.get("duration_seconds"),
            transcript=payload.get("transcript"),
            recording_url=payload.get("recording_url"),
            vacancy_status=vacancy,
            foreigner_accepted=_to_bool(foreigner) if foreigner is not None else None,
            chinese_accepted=_to_bool(chinese) if chinese is not None else None,
            special_conditions=conditions,
        )

    @property
    def supports_batch(self) -> bool:
        return bool(self.flow_agent_id)

    @property
    def supports_phone_call(self) -> bool:
        return True


class MockProvider(VoiceProvider):
    """Tier 1 test provider. No real phone calls."""

    def __init__(self, config: dict):
        self.config = config

    def create_call(
        self,
        phone_number: str,
        property_name: str,
        property_id: str,
        mode: str = "default",
    ) -> CallResult:
        raise NotImplementedError(
            "Tier 1 (Free) では実際の電話発信はできません。Web Call を使用してください。"
        )

    def create_web_call(
        self,
        property_name: str,
        property_id: str,
    ) -> WebCallResult:
        return WebCallResult(
            call_id=f"mock_{uuid4().hex[:8]}",
            access_token=f"mock_token_{uuid4().hex[:8]}",
        )

    def get_call_status(self, call_id: str) -> CallStatus:
        if call_id.startswith("mock_"):
            return CallStatus(
                call_id=call_id,
                status="completed",
                duration_seconds=60,
                transcript="[Mock] テスト通話トランスクリプト",
            )
        raise ValueError(f"Unknown mock call: {call_id}")

    def parse_webhook(self, payload: dict) -> WebhookResult:
        return WebhookResult(
            call_id=payload.get("call_id", ""),
            call_status=payload.get("call_status", "unknown"),
        )

    @property
    def supports_batch(self) -> bool:
        return False

    @property
    def supports_phone_call(self) -> bool:
        return False


# ── Feature flags per tier ──

TIER_FEATURES: dict[str, set[str]] = {
    "free": {
        "web_call", "template_edit", "email",
    },
    "lightweight": {
        "web_call", "phone_call", "template_edit", "email",
        "budget_mode", "webhook", "line_notify", "analytics_basic",
    },
    "full": {
        "web_call", "phone_call", "template_edit", "email",
        "budget_mode", "flow_mode", "webhook", "line_notify",
        "analytics_basic", "analytics_advanced", "batch_call",
        "kpi_dashboard", "provider_bland", "advanced_denoising",
    },
}


def is_feature_enabled(config: dict, feature: str) -> bool:
    tier = config.get("tier", "free")
    return feature in TIER_FEATURES.get(tier, set())


def get_voice_provider(config: dict | None = None) -> VoiceProvider:
    """Factory: create a VoiceProvider based on config."""
    if config is None:
        config = load_config()

    provider_name = config.get("voice_provider", "retell")
    tier = config.get("tier", "free")

    if tier == "free" and not config.get("retell_api_key"):
        return MockProvider(config)

    if provider_name == "retell" and config.get("retell_api_key"):
        return RetellProvider(config)

    return MockProvider(config)
