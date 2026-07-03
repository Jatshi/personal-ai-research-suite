from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_console_script_and_metadata():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "personal-ai-workspace"
    assert data["project"]["scripts"]["personal-ai-workspace"] == "personal_ai_workspace.cli:main"
    assert "chromadb>=0.5.0" in data["project"]["optional-dependencies"]["production"]
    assert data["tool"]["setuptools"]["packages"]["find"]["include"] == ["personal_ai_workspace*"]
