from __future__ import annotations


def write_operation_plan(path: str, content: str, overwrite: bool, dry_run: bool, confirm: bool) -> dict:
    return {
        "operation": "write_file",
        "path": path,
        "bytes": len(content.encode("utf-8")),
        "overwrite": overwrite,
        "dry_run": dry_run,
        "confirm": confirm,
    }

