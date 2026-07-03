from __future__ import annotations

from src.config.config_loader import load_config
from src.mcp_servers.combined_server import build_registry


def test_client_like_registry_call() -> None:
    registry = build_registry(load_config())
    tools = registry.list_tools()
    assert any(t["name"] == "list_files" for t in tools)
    res = registry.call("list_files", {"path": "."})
    assert res["success"]

