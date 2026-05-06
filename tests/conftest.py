from __future__ import annotations

import pytest


@pytest.fixture
def free_config() -> dict:
    return {
        "tier": "free",
        "voice_provider": "retell",
        "retell_api_key": "",
        "retell_agent_id": "",
        "retell_agent_id_budget": "",
        "retell_agent_id_flow": "",
        "bland_api_key": "",
        "bland_pathway_id": "",
        "openai_api_key": "test-openai-key",
        "gmail_address": "",
        "gmail_app_password": "",
        "company_name": "テスト不動産",
        "contact_person": "",
        "phone_number": "",
        "email_signature": "",
        "line_channel_access_token": "",
        "line_user_id": "",
        "base_url": "http://localhost:8000",
    }


@pytest.fixture
def lightweight_config(free_config) -> dict:
    cfg = free_config.copy()
    cfg.update({
        "tier": "lightweight",
        "retell_api_key": "test_retell_key_abc",
        "retell_agent_id": "agent_default_123",
        "retell_agent_id_budget": "agent_budget_456",
    })
    return cfg


@pytest.fixture
def full_config(lightweight_config) -> dict:
    cfg = lightweight_config.copy()
    cfg.update({
        "tier": "full",
        "retell_agent_id_flow": "agent_flow_789",
        "bland_api_key": "test_bland_key",
        "bland_pathway_id": "test_pathway",
    })
    return cfg
