from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from src.observability.trace_logger import log_event
from src.safety.path_guard import PathGuard


def write_note_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = PathGuard(config).resolve(args.get("path", "notes/new_note.md"), for_write=True)
    plan = {"operation": "write_note", "path": str(path), "bytes": len(args.get("content", "")), "dry_run": args.get("dry_run", True)}
    if args.get("dry_run", True):
        return {"success": True, "executed": False, "plan": plan}
    path.write_text(args.get("content", ""), encoding="utf-8")
    log_event(config, "audit_log.jsonl", {"operation": "write_note", "path": str(path), "confirmed": args.get("confirmed", False)})
    return {"success": True, "executed": True, "plan": plan}

