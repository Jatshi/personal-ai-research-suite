from __future__ import annotations

import pytest

from src.config.config_loader import load_config
from src.integrations.agent_workspace_bridge import _agent_workspace_root, _safe_relative_path


def test_agent_workspace_bridge_rejects_escape_paths():
    with pytest.raises(ValueError):
        _safe_relative_path("../outside")
    with pytest.raises(ValueError):
        _safe_relative_path("C:/outside")
    with pytest.raises(ValueError):
        _safe_relative_path("papers/demo.md")
    assert _safe_relative_path("workspace/papers/demo.md") == "workspace/papers/demo.md"


def test_agent_workspace_root_is_resolved_from_project_config():
    assert (_agent_workspace_root(load_config()) / "src" / "cli.py").exists()
