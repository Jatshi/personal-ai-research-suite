from __future__ import annotations

from pathlib import Path
from typing import Any

from src.safety.path_guard import PathGuard


def list_files_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    guard = PathGuard(config)
    root = guard.resolve(args.get("path", "."), must_exist=True)
    recursive = bool(args.get("recursive", True))
    files = []
    iterator = root.rglob("*") if recursive and root.is_dir() else root.iterdir() if root.is_dir() else [root]
    for p in iterator:
        try:
            rp = p.resolve().relative_to(guard.workspace)
        except ValueError:
            continue
        files.append({"path": str(rp), "name": p.name, "is_dir": p.is_dir(), "size_bytes": p.stat().st_size if p.exists() else 0})
    return {"success": True, "files": files}


def read_file_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = PathGuard(config).resolve(args["path"], must_exist=True)
    return {"success": True, "path": str(path), "content": path.read_text(encoding="utf-8", errors="ignore")}

