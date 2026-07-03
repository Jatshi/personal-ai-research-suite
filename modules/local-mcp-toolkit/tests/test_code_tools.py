from __future__ import annotations

from src.config.config_loader import load_config
from src.mcp_servers.combined_server import build_registry


def test_repo_tree_skips_ignored_dirs() -> None:
    registry = build_registry(load_config(), ["code"])
    res = registry.call("list_repo_tree", {"repo_path": "sample_repo", "max_depth": 4})
    assert res["success"]
    text = str(res["data"]["tree"])
    assert ".git" not in text
    assert "node_modules" not in text


def test_search_code_and_find_todos() -> None:
    registry = build_registry(load_config(), ["code"])
    search = registry.call("search_code", {"repo_path": "sample_repo", "query": "TODO"})
    todos = registry.call("find_todos", {"repo_path": "sample_repo"})
    assert search["success"] and search["data"]["matches"]
    assert todos["success"] and todos["data"]["todos"]

