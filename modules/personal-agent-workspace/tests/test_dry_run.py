from __future__ import annotations

from pathlib import Path

from src.safety.audit_log import JsonlAuditLog
from src.safety.path_guard import PathGuard
from src.tools.file_tools import rename_file
from src.safety.rollback import RollbackStore


def test_rename_dry_run_does_not_change_file(cfg: dict) -> None:
    path = Path(cfg["app"]["workspace_dir"]) / "messy_files" / "random_report_v3.txt"
    result = rename_file(str(path), "renamed.txt", PathGuard(cfg["app"]["workspace_dir"]), JsonlAuditLog(Path(cfg["app"]["workspace_dir"]) / "audit.jsonl"), RollbackStore(Path(cfg["app"]["workspace_dir"]) / "rollback.jsonl"), dry_run=True)
    assert result["dry_run"]
    assert path.exists()

