from __future__ import annotations

from pathlib import Path

from src.safety.audit_log import JsonlAuditLog
from src.safety.path_guard import PathGuard
from src.safety.rollback import RollbackStore
from src.tools.file_tools import delete_file, scan_folder


def test_scan_returns_metadata_and_duplicates(cfg: dict) -> None:
    guard = PathGuard(cfg["app"]["workspace_dir"])
    result = scan_folder("messy_files", cfg["file_organizer"]["allowed_extensions"], guard)
    assert result["files"]
    assert result["duplicates"]
    assert "hash" in result["files"][0]


def test_dry_run_delete_does_not_delete(cfg: dict) -> None:
    guard = PathGuard(cfg["app"]["workspace_dir"])
    path = Path(cfg["app"]["workspace_dir"]) / "messy_files" / "random_report_v3.txt"
    out = delete_file(str(path), guard, JsonlAuditLog(Path(cfg["app"]["workspace_dir"]) / "audit.jsonl"), dry_run=True)
    assert out["dry_run"]
    assert path.exists()

