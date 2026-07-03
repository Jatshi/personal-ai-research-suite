import os

from src.cli import doctor_config
from src.config.config_loader import load_config


def test_doctor_config_default_passes():
    report = doctor_config(load_config())
    assert report["success"] is True
    assert report["errors"] == []


def test_doctor_config_production_requires_secrets(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PERSONAL_AI_API_TOKEN", raising=False)
    cfg = load_config("config.production.yaml")
    report = doctor_config(cfg)
    assert report["success"] is False
    assert any("API token" in e for e in report["errors"])
    assert any("LLM API key" in e for e in report["errors"])
