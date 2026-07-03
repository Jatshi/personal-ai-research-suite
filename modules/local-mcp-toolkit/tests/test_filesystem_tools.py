from __future__ import annotations

from pathlib import Path

from src.config.config_loader import load_config, resolve_path
from src.mcp_servers.combined_server import build_registry


def test_write_file_dry_run_and_confirm() -> None:
    workspace = resolve_path(load_config(), "./examples/workspace")
    confirmed = workspace / "notes" / "confirmed_test.md"
    if confirmed.exists():
        confirmed.unlink()
    registry = build_registry(load_config(), ["filesystem"])
    dry = registry.call("write_file", {"path": "notes/dry_run.md", "content": "hello"})
    assert not (resolve_path(load_config(), "./examples/workspace") / "notes" / "dry_run.md").exists()
    assert dry["success"]
    no_confirm = registry.call("write_file", {"path": "notes/no_confirm.md", "content": "hello", "dry_run": False})
    assert not no_confirm["success"]
    ok = registry.call("write_file", {"path": "notes/confirmed_test.md", "content": "hello", "dry_run": False, "confirm": True})
    assert ok["success"]
    assert confirmed.exists()


def test_audit_log_records_tool_call() -> None:
    cfg = load_config()
    registry = build_registry(cfg, ["filesystem"])
    res = registry.call("list_files", {"path": "."})
    assert res["success"]
    assert resolve_path(cfg, cfg["logging"]["tool_call_log"]).exists()
