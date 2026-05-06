from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.services.voice_provider import MockProvider, RetellProvider


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config_manager.CONFIG_PATH", tmp_path / "config.yaml")
    monkeypatch.setattr("app.database.DB_PATH", tmp_path / "data.db")

    from app.database import init_db
    init_db()

    from app.main import app
    return TestClient(app)


@pytest.fixture
def client_with_mock(client, free_config):
    mock = MockProvider(free_config)
    with patch("app.api.calls._get_provider", return_value=mock):
        yield client


@pytest.fixture
def client_with_retell(client, lightweight_config):
    provider = RetellProvider(lightweight_config)
    with patch("app.api.calls._get_provider", return_value=provider):
        yield client


# ── POST /calls/webhook ──


class TestWebhook:

    def test_webhook_returns_ok(self, client_with_mock):
        payload = {
            "call_id": "call_123",
            "call_status": "ended",
            "duration_seconds": 90,
            "transcript": "テスト",
        }
        resp = client_with_mock.post("/calls/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_webhook_retell_alias(self, client_with_mock):
        payload = {"call_id": "c1", "call_status": "completed"}
        resp = client_with_mock.post("/calls/webhook/retell", json=payload)
        assert resp.status_code == 200

    def test_webhook_with_analysis(self, client_with_mock):
        payload = {
            "call_id": "call_abc",
            "call_status": "ended",
            "duration_seconds": 120,
            "call_analysis": {
                "custom_analysis_data": {
                    "vacancy_status": "あり",
                    "foreigner_accepted": "true",
                    "chinese_accepted": "yes",
                    "special_conditions": "保証会社必須",
                }
            },
        }
        resp = client_with_mock.post("/calls/webhook", json=payload)
        assert resp.status_code == 200


# ── POST /calls/batch-trigger ──


class TestBatchTrigger:

    def test_batch_blocked_for_free_tier(self, client_with_mock, monkeypatch):
        monkeypatch.setenv("TIER", "free")
        resp = client_with_mock.post("/calls/batch-trigger", json={
            "property_ids": ["00000000-0000-0000-0000-000000000001"],
        })
        assert resp.status_code == 403

    def test_batch_blocked_for_mock_provider(self, client_with_mock, monkeypatch):
        monkeypatch.setenv("TIER", "full")
        resp = client_with_mock.post("/calls/batch-trigger", json={
            "property_ids": ["00000000-0000-0000-0000-000000000001"],
        })
        assert resp.status_code == 400


# ── POST /calls/trigger ──


class TestTriggerCall:

    def test_trigger_nonexistent_property(self, client_with_mock):
        resp = client_with_mock.post("/calls/trigger", json={
            "property_id": "00000000-0000-0000-0000-000000000099",
        })
        assert resp.status_code == 404


# ── GET /calls/{property_id} ──


class TestGetCallRecords:

    def test_returns_empty_for_new_property(self, client_with_mock):
        prop_id = "00000000-0000-0000-0000-000000000001"
        resp = client_with_mock.get(f"/calls/{prop_id}")
        assert resp.status_code == 200
        assert resp.json() == []
