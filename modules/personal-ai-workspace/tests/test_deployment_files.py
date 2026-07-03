from pathlib import Path

import yaml

from src.config.config_loader import load_config


ROOT = Path(__file__).resolve().parents[1]


def test_docker_artifacts_exist_and_compose_is_valid_yaml():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "Dockerfile.production").exists()
    assert (ROOT / ".dockerignore").exists()
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert {"api", "streamlit"} <= set(compose["services"])
    assert "8000:8000" in compose["services"]["api"]["ports"]
    assert "8501:8501" in compose["services"]["streamlit"]["ports"]
    prod = yaml.safe_load((ROOT / "docker-compose.production.yml").read_text(encoding="utf-8"))
    assert prod["services"]["api"]["build"]["dockerfile"] == "Dockerfile.production"
    assert "./config.production.yaml:/app/config.yaml:ro" in prod["services"]["api"]["volumes"]


def test_production_config_enables_real_backends_and_api_auth():
    cfg = yaml.safe_load((ROOT / "config.production.yaml").read_text(encoding="utf-8"))
    assert cfg["app"]["mock_mode"] is False
    assert cfg["server"]["api_auth_enabled"] is True
    assert cfg["llm"]["backend"] == "openai"
    assert cfg["embedding"]["backend"] == "openai"
    assert cfg["vector_store"]["backend"] == "chroma"


def test_config_can_be_selected_with_environment(monkeypatch):
    monkeypatch.setenv("PERSONAL_AI_CONFIG", "config.production.yaml")
    cfg = load_config()
    assert cfg["_config_path"].endswith("config.production.yaml")
    assert cfg["vector_store"]["backend"] == "chroma"
