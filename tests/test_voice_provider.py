from __future__ import annotations

import pytest

from app.services.voice_provider import (
    CallResult,
    CallStatus,
    MockProvider,
    RetellProvider,
    WebCallResult,
    WebhookResult,
    get_voice_provider,
    is_feature_enabled,
)


# ── MockProvider ──


class TestMockProvider:

    def test_init(self, free_config):
        p = MockProvider(free_config)
        assert p.config is free_config

    def test_create_call_raises(self, free_config):
        p = MockProvider(free_config)
        with pytest.raises(NotImplementedError, match="Tier 1"):
            p.create_call("03-1234-5678", "テスト物件", "prop-1")

    def test_create_web_call(self, free_config):
        p = MockProvider(free_config)
        result = p.create_web_call("テスト物件", "prop-1")
        assert isinstance(result, WebCallResult)
        assert result.call_id.startswith("mock_")
        assert result.access_token.startswith("mock_token_")

    def test_get_call_status_mock(self, free_config):
        p = MockProvider(free_config)
        status = p.get_call_status("mock_abc12345")
        assert isinstance(status, CallStatus)
        assert status.call_id == "mock_abc12345"
        assert status.status == "completed"
        assert status.duration_seconds == 60

    def test_get_call_status_unknown(self, free_config):
        p = MockProvider(free_config)
        with pytest.raises(ValueError, match="Unknown mock call"):
            p.get_call_status("real_call_123")

    def test_parse_webhook(self, free_config):
        p = MockProvider(free_config)
        result = p.parse_webhook({"call_id": "c1", "call_status": "ended"})
        assert isinstance(result, WebhookResult)
        assert result.call_id == "c1"
        assert result.call_status == "ended"

    def test_supports_batch_false(self, free_config):
        assert MockProvider(free_config).supports_batch is False

    def test_supports_phone_call_false(self, free_config):
        assert MockProvider(free_config).supports_phone_call is False

    def test_provider_name(self, free_config):
        assert MockProvider(free_config).provider_name == "MockProvider"


# ── RetellProvider ──


class TestRetellProvider:

    def test_init(self, lightweight_config):
        p = RetellProvider(lightweight_config)
        assert p.api_key == "test_retell_key_abc"
        assert p.agent_id == "agent_default_123"
        assert p.budget_agent_id == "agent_budget_456"
        assert p.flow_agent_id == ""

    def test_select_agent_default(self, lightweight_config):
        p = RetellProvider(lightweight_config)
        assert p._select_agent("default") == "agent_default_123"

    def test_select_agent_budget(self, lightweight_config):
        p = RetellProvider(lightweight_config)
        assert p._select_agent("budget") == "agent_budget_456"

    def test_select_agent_budget_fallback(self, free_config):
        cfg = free_config.copy()
        cfg["retell_api_key"] = "key"
        cfg["retell_agent_id"] = "main"
        p = RetellProvider(cfg)
        assert p._select_agent("budget") == "main"

    def test_select_agent_flow(self, full_config):
        p = RetellProvider(full_config)
        assert p._select_agent("flow") == "agent_flow_789"

    def test_to_e164_leading_zero(self):
        assert RetellProvider._to_e164("03-1234-5678") == "+81312345678"

    def test_to_e164_with_spaces(self):
        assert RetellProvider._to_e164("090 1234 5678") == "+819012345678"

    def test_to_e164_already_international(self):
        assert RetellProvider._to_e164("+81312345678") == "+81312345678"

    def test_to_e164_plain_number(self):
        assert RetellProvider._to_e164("1234567890") == "+1234567890"

    def test_supports_batch_with_flow(self, full_config):
        assert RetellProvider(full_config).supports_batch is True

    def test_supports_batch_without_flow(self, lightweight_config):
        assert RetellProvider(lightweight_config).supports_batch is False

    def test_supports_phone_call(self, lightweight_config):
        assert RetellProvider(lightweight_config).supports_phone_call is True

    def test_parse_webhook_full(self, lightweight_config):
        p = RetellProvider(lightweight_config)
        payload = {
            "call_id": "call_abc",
            "call_status": "ended",
            "duration_seconds": 120,
            "transcript": "テストトランスクリプト",
            "recording_url": "https://example.com/rec.mp3",
            "call_analysis": {
                "custom_analysis_data": {
                    "vacancy_status": "あり",
                    "foreigner_accepted": "true",
                    "chinese_accepted": "可",
                    "special_conditions": "保証会社必須",
                }
            },
        }
        result = p.parse_webhook(payload)
        assert result.call_id == "call_abc"
        assert result.call_status == "ended"
        assert result.duration_seconds == 120
        assert result.vacancy_status == "あり"
        assert result.foreigner_accepted is True
        assert result.chinese_accepted is True
        assert result.special_conditions == "保証会社必須"

    def test_parse_webhook_japanese_bool(self, lightweight_config):
        p = RetellProvider(lightweight_config)
        payload = {
            "call_id": "c1",
            "call_status": "ended",
            "call_analysis": {
                "custom_analysis_data": {
                    "foreigner_accepted": "不可",
                    "chinese_accepted": "yes",
                }
            },
        }
        result = p.parse_webhook(payload)
        assert result.foreigner_accepted is False
        assert result.chinese_accepted is True

    def test_parse_webhook_empty_analysis(self, lightweight_config):
        p = RetellProvider(lightweight_config)
        result = p.parse_webhook({"call_id": "c1", "call_status": "ended"})
        assert result.call_id == "c1"
        assert result.vacancy_status is None
        assert result.foreigner_accepted is None

    def test_provider_name(self, lightweight_config):
        assert RetellProvider(lightweight_config).provider_name == "RetellProvider"


# ── Factory ──


class TestGetVoiceProvider:

    def test_free_no_key_returns_mock(self, free_config):
        p = get_voice_provider(free_config)
        assert isinstance(p, MockProvider)

    def test_with_retell_key_returns_retell(self, lightweight_config):
        p = get_voice_provider(lightweight_config)
        assert isinstance(p, RetellProvider)

    def test_free_with_key_returns_retell(self, free_config):
        cfg = free_config.copy()
        cfg["retell_api_key"] = "some_key"
        cfg["retell_agent_id"] = "some_agent"
        p = get_voice_provider(cfg)
        assert isinstance(p, RetellProvider)

    def test_unknown_provider_returns_mock(self, free_config):
        cfg = free_config.copy()
        cfg["voice_provider"] = "unknown_provider"
        p = get_voice_provider(cfg)
        assert isinstance(p, MockProvider)


# ── Feature Flags ──


class TestFeatureFlags:

    def test_free_features(self, free_config):
        assert is_feature_enabled(free_config, "web_call") is True
        assert is_feature_enabled(free_config, "phone_call") is False
        assert is_feature_enabled(free_config, "batch_call") is False

    def test_lightweight_features(self, lightweight_config):
        assert is_feature_enabled(lightweight_config, "phone_call") is True
        assert is_feature_enabled(lightweight_config, "budget_mode") is True
        assert is_feature_enabled(lightweight_config, "batch_call") is False

    def test_full_features(self, full_config):
        assert is_feature_enabled(full_config, "batch_call") is True
        assert is_feature_enabled(full_config, "flow_mode") is True
        assert is_feature_enabled(full_config, "provider_bland") is True

    def test_unknown_tier(self):
        assert is_feature_enabled({"tier": "premium"}, "web_call") is False

    def test_missing_tier_defaults_free(self):
        assert is_feature_enabled({}, "web_call") is True
        assert is_feature_enabled({}, "phone_call") is False
