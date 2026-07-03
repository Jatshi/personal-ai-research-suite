from __future__ import annotations

from src.tools.default_registry import build_registry


def test_file_organizer_plan_contains_summary_and_operations(cfg: dict) -> None:
    registry = build_registry(cfg)
    result = registry.call("organize_files", {"path": "messy_files"}, dry_run=True)
    assert result.success
    assert result.output["files"]
    assert "summary" in result.output["files"][0]
    assert result.output["dry_run_operations"]

