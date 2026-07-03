from __future__ import annotations

from pathlib import Path

from src.safety.audit_log import JsonlAuditLog


def test_audit_log_roundtrip(tmp_path: Path) -> None:
    log = JsonlAuditLog(tmp_path / "audit.jsonl")
    log.write({"tool_name": "demo", "success": True})
    rows = log.read()
    assert rows and rows[0]["tool_name"] == "demo"

