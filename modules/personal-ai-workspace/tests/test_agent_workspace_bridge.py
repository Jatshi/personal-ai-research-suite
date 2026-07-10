from __future__ import annotations

import pytest

from src.config.config_loader import load_config
from src.integrations.agent_workspace_bridge import _agent_workspace_root, _operations_hash, _safe_relative_path


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


def test_approval_operation_hash_is_stable_and_order_sensitive():
    operation = {"operation": "rename_file", "source": "workspace/a.txt", "new_name": "b.txt"}
    assert _operations_hash([operation]) == _operations_hash([dict(operation)])
    assert _operations_hash([operation]) != _operations_hash([])
