from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.config_manager import (
    DEFAULTS,
    ENV_MAP,
    load_config,
    save_config,
)


class TestLoadConfig:

    def test_returns_defaults_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config_manager.CONFIG_PATH", tmp_path / "nonexistent.yaml")
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        assert cfg["tier"] == "free"
        assert cfg["voice_provider"] == "retell"

    def test_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config_manager.CONFIG_PATH", tmp_path / "nonexistent.yaml")
        env = {"TIER": "full", "VOICE_PROVIDER": "bland", "RETELL_API_KEY": "env_key"}
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert cfg["tier"] == "full"
        assert cfg["voice_provider"] == "bland"
        assert cfg["retell_api_key"] == "env_key"

    def test_file_values_merge_with_defaults(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("tier: lightweight\ncompany_name: テスト会社\n")
        monkeypatch.setattr("app.config_manager.CONFIG_PATH", config_file)
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        assert cfg["tier"] == "lightweight"
        assert cfg["company_name"] == "テスト会社"
        assert cfg["voice_provider"] == "retell"

    def test_auto_upgrade_free_to_lightweight(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("tier: free\nretell_api_key: real_key\nretell_agent_id: real_agent\n")
        monkeypatch.setattr("app.config_manager.CONFIG_PATH", config_file)
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        assert cfg["tier"] == "lightweight", "Should auto-upgrade when Retell key + agent exist"

    def test_no_auto_upgrade_without_agent_id(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("tier: free\nretell_api_key: real_key\n")
        monkeypatch.setattr("app.config_manager.CONFIG_PATH", config_file)
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        assert cfg["tier"] == "free", "Should NOT upgrade without agent_id"


class TestSaveConfig:

    def test_saves_only_known_keys(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        monkeypatch.setattr("app.config_manager.CONFIG_PATH", config_file)
        save_config({"tier": "full", "unknown_key": "should_be_dropped"})
        import yaml
        with open(config_file) as f:
            saved = yaml.safe_load(f)
        assert "unknown_key" not in saved
        assert saved["tier"] == "full"


class TestDefaults:

    def test_all_env_map_keys_in_defaults(self):
        for key in ENV_MAP:
            assert key in DEFAULTS, f"ENV_MAP key '{key}' missing from DEFAULTS"

    def test_defaults_has_all_required_keys(self):
        required = {"tier", "voice_provider", "retell_api_key", "retell_agent_id",
                    "retell_agent_id_budget", "retell_agent_id_flow", "bland_api_key",
                    "bland_pathway_id", "openai_api_key", "company_name"}
        assert required.issubset(set(DEFAULTS.keys()))
