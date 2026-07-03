from __future__ import annotations

import re
from typing import Any

from src.observability.trace_logger import log_event
from src.safety.path_guard import PathGuard


def parse_todo(content: str) -> list[dict[str, Any]]:
    tasks = []
    for line in content.splitlines():
        m = re.match(r"\s*-\s+\[( |x|X)\]\s+(.*)", line)
        if not m:
            continue
        body = m.group(2)
        tasks.append(
            {
                "done": m.group(1).lower() == "x",
                "text": body,
                "priority": re.search(r"priority:([A-Za-z0-9_-]+)", body).group(1) if re.search(r"priority:([A-Za-z0-9_-]+)", body) else "",
                "deadline": re.search(r"deadline:([0-9-]+)", body).group(1) if re.search(r"deadline:([0-9-]+)", body) else "",
            }
        )
    return tasks


def read_todo_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = PathGuard(config).resolve(args.get("path", "todo.md"), must_exist=True)
    content = path.read_text(encoding="utf-8", errors="ignore")
    return {"success": True, "path": str(path), "tasks": parse_todo(content), "content": content}


def write_todo_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = PathGuard(config).resolve(args.get("path", "todo.md"), for_write=True)
    plan = {"operation": "write_todo", "path": str(path), "dry_run": args.get("dry_run", True)}
    if args.get("dry_run", True):
        return {"success": True, "executed": False, "plan": plan, "content": args.get("content", "")}
    path.write_text(args.get("content", ""), encoding="utf-8")
    log_event(config, "audit_log.jsonl", {"operation": "write_todo", "path": str(path), "confirmed": args.get("confirmed", False)})
    return {"success": True, "executed": True, "plan": plan}

