from pathlib import Path

import yaml

from src.config.config_loader import load_config


ROOT = Path(__file__).resolve().parents[1]


def test_docker_artifacts_exist_and_compose_is_valid_yaml():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / ".dockerignore").exists()
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert "mcp" in compose["services"]
    assert compose["services"]["mcp"]["command"] == "python -m src.cli serve --server combined"


def test_local_project_config_template_uses_real_rag_bridge():
    cfg = yaml.safe_load((ROOT / "config.local_project.example.yaml").read_text(encoding="utf-8"))
    assert cfg["rag"]["backend"] == "local_project"
    assert cfg["rag"]["project_path"] == "../personal-ai-workspace"
    assert cfg["rag"]["project_config"] == "config.yaml"
    assert cfg["security"]["block_sensitive_files"] is True


def test_config_can_be_selected_with_environment(monkeypatch):
    monkeypatch.setenv("LOCAL_MCP_CONFIG", "config.local_project.example.yaml")
    cfg = load_config()
    assert cfg["_config_path"].endswith("config.local_project.example.yaml")
    assert cfg["rag"]["backend"] == "local_project"
