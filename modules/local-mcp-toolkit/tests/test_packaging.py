from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_console_script_and_metadata():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "local-mcp-toolkit"
    assert data["project"]["scripts"]["local-mcp-toolkit"] == "local_mcp_toolkit.cli:main"
    assert "mcp>=1.9.0" in data["project"]["optional-dependencies"]["mcp"]
    assert data["tool"]["setuptools"]["packages"]["find"]["include"] == ["local_mcp_toolkit*"]
