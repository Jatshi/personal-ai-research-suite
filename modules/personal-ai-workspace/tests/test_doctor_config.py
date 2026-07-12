import os

from src.cli import doctor_config
from src.config.config_loader import load_config


def test_doctor_config_default_passes():
    report = doctor_config(load_config())
    assert report["success"] is True
    assert report["errors"] == []


def test_doctor_config_production_requires_secrets(monkeypatch):
    cfg = load_config("config.production.yaml")
    # load_config intentionally loads the local .env file. Use dedicated absent
    # variable names so this test remains isolated from developer credentials.
    cfg["llm"]["api_key_env"] = "PERSONAL_AI_TEST_MISSING_LLM_KEY"
    cfg["embedding"]["api_key_env"] = "PERSONAL_AI_TEST_MISSING_EMBEDDING_KEY"
    cfg["server"]["api_token_env"] = "PERSONAL_AI_TEST_MISSING_API_TOKEN"
    monkeypatch.delenv("PERSONAL_AI_TEST_MISSING_LLM_KEY", raising=False)
    monkeypatch.delenv("PERSONAL_AI_TEST_MISSING_EMBEDDING_KEY", raising=False)
    monkeypatch.delenv("PERSONAL_AI_TEST_MISSING_API_TOKEN", raising=False)
    report = doctor_config(cfg)
    assert report["success"] is False
    assert any("API token" in e for e in report["errors"])
    assert any("LLM API key" in e for e in report["errors"])
