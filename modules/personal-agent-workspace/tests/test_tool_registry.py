from __future__ import annotations

from pathlib import Path

from src.tools.default_registry import build_registry


def test_registry_calls_tool_and_logs(cfg: dict) -> None:
    registry = build_registry(cfg)
    result = registry.call("scan_folder", {"path": "messy_files"})
    assert result.success
    log_path = Path(cfg["logging"]["tool_log_file"])
    assert log_path.exists()


def test_high_risk_requires_confirmation(cfg: dict) -> None:
    registry = build_registry(cfg)
    result = registry.call("rename_file", {"source": "messy_files/random_report_v3.txt", "new_name": "renamed.txt"}, dry_run=False)
    assert not result.success
    assert result.requires_confirmation

