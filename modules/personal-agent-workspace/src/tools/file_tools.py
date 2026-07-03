from __future__ import annotations

import os
import re
import shutil
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from src.llm.base import BaseLLMClient
from src.safety.audit_log import JsonlAuditLog
from src.safety.path_guard import PathGuard
from src.safety.rollback import RollbackStore
from src.storage.sqlite_store import WorkspaceSQLiteStore
from src.tools.document_tools import read_document
from src.utils.file_utils import CODE_EXTENSIONS, DOC_EXTENSIONS, IMAGE_EXTENSIONS, human_size
from src.utils.hash_utils import file_sha256
from src.utils.text_utils import clean_text, extract_year, top_keywords


def scan_folder(path: str, allowed_extensions: list[str], guard: PathGuard, store: WorkspaceSQLiteStore | None = None) -> dict:
    root = guard.validate(path, must_exist=True)
    files = []
    allowed = set(allowed_extensions)
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in allowed:
            continue
        try:
            stat = p.stat()
            files.append(
                {
                    "filename": p.name,
                    "path": str(p),
                    "extension": p.suffix.lower(),
                    "size": stat.st_size,
                    "size_human": human_size(stat.st_size),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    "hash": file_sha256(p),
                    "is_temp": p.name.startswith("~") or p.suffix.lower() in {".tmp", ".bak"},
                    "is_empty_or_abnormal": stat.st_size == 0,
                }
            )
        except Exception as exc:
            files.append({"filename": p.name, "path": str(p), "error": str(exc)})
    duplicates = find_duplicates_from_manifest(files)
    duplicate_paths = {item["path"] for group in duplicates for item in group["files"]}
    for item in files:
        item["is_duplicate"] = item.get("path") in duplicate_paths
    if store:
        store.upsert_files(files)
    return {"root": str(root), "files": files, "duplicates": duplicates}


def find_duplicates(path: str, allowed_extensions: list[str], guard: PathGuard, store: WorkspaceSQLiteStore | None = None) -> dict:
    return {"duplicates": scan_folder(path, allowed_extensions, guard, store)["duplicates"]}


def find_duplicates_from_manifest(files: list[dict]) -> list[dict]:
    groups: list[dict] = []
    by_hash: dict[str, list[dict]] = defaultdict(list)
    for item in files:
        if item.get("hash"):
            by_hash[item["hash"]].append(item)
    for digest, items in by_hash.items():
        if len(items) > 1:
            groups.append({"reason": "same_hash", "hash": digest, "files": items})
    for i, a in enumerate(files):
        for b in files[i + 1 :]:
            if a.get("hash") == b.get("hash"):
                continue
            ratio = SequenceMatcher(None, Path(a.get("filename", "")).stem.lower(), Path(b.get("filename", "")).stem.lower()).ratio()
            same_size_time = a.get("size") == b.get("size") and a.get("modified_time") == b.get("modified_time")
            if ratio > 0.88 or same_size_time:
                groups.append({"reason": "similar_name_or_size_time", "similarity": round(ratio, 3), "files": [a, b]})
    return groups


def suggest_file_category(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    name = p.name.lower()
    text = ""
    if ext in DOC_EXTENSIONS | CODE_EXTENSIONS:
        text = clean_text(read_document(str(p)).get("text", ""))[:3000].lower()
    signals = f"{name} {text}"
    if ext in CODE_EXTENSIONS:
        return "code"
    if ext == ".pptx" or "slide" in signals or "slides" in signals:
        return "slides"
    if any(x in signals for x in ["thesis", "dissertation", "博士", "论文"]):
        return "dissertation"
    if any(x in signals for x in ["abstract", "method", "experiment", "references", "paper", "文献"]):
        return "papers"
    if any(x in signals for x in ["resume", "cv", "career", "求职", "简历"]):
        return "job_search"
    if any(x in signals for x in ["report", "summary", "日报", "周报"]):
        return "reports"
    if any(x in signals for x in ["project", "app", "system", "项目"]):
        return "projects"
    if ext in {".md", ".txt"}:
        return "notes"
    return "unknown"


def suggest_file_rename(path: str) -> dict:
    p = Path(path)
    text = clean_text(read_document(str(p)).get("text", ""))[:2500]
    year = extract_year(p.name + " " + text)
    category = suggest_file_category(str(p))
    keywords = top_keywords(p.stem + " " + text, 3)
    topic = "_".join(keywords) if keywords else re.sub(r"\W+", "_", p.stem)[:30]
    return {"path": str(p), "suggested_name": f"{year}_{category}_{topic}_v1{p.suffix}", "category": category}


def move_file(source: str, target: str, guard: PathGuard, audit_log: JsonlAuditLog, rollback: RollbackStore, dry_run: bool = True, confirmed: bool = False) -> dict:
    src = guard.validate(source, must_exist=True)
    dst = guard.validate(target, for_write=True)
    plan = {"operation": "move_file", "source": str(src), "target": str(dst), "dry_run": dry_run}
    audit_log.write(plan | {"executed": False})
    if dry_run:
        return plan
    if not confirmed:
        raise PermissionError("move_file requires confirmation")
    shutil.move(str(src), str(dst))
    rollback.append({"operation": "move_file", "rollback": {"source": str(dst), "target": str(src)}})
    audit_log.write(plan | {"executed": True})
    return plan | {"executed": True}


def rename_file(source: str, new_name: str, guard: PathGuard, audit_log: JsonlAuditLog, rollback: RollbackStore, dry_run: bool = True, confirmed: bool = False) -> dict:
    src = guard.validate(source, must_exist=True)
    if Path(new_name).name != new_name:
        raise ValueError("new_name must be a filename, not a path")
    dst = src.with_name(new_name)
    guard.validate(dst, for_write=True)
    plan = {"operation": "rename_file", "source": str(src), "target": str(dst), "new_name": new_name, "dry_run": dry_run}
    audit_log.write(plan | {"executed": False})
    if dry_run:
        return plan
    if not confirmed:
        raise PermissionError("rename_file requires confirmation")
    shutil.move(str(src), str(dst))
    rollback.append({"operation": "rename_file", "rollback": {"source": str(dst), "new_name": src.name}})
    audit_log.write(plan | {"executed": True})
    return plan | {"executed": True}


def delete_file(path: str, guard: PathGuard, audit_log: JsonlAuditLog, dry_run: bool = True, confirmed: bool = False, allow_delete: bool = False) -> dict:
    p = guard.validate(path, must_exist=True)
    plan = {"operation": "delete_file", "path": str(p), "dry_run": dry_run}
    audit_log.write(plan | {"executed": False})
    if dry_run:
        return plan
    if not allow_delete:
        raise PermissionError("delete_file is disabled by config")
    if not confirmed:
        raise PermissionError("delete_file requires confirmation")
    os.remove(p)
    audit_log.write(plan | {"executed": True})
    return plan | {"executed": True}


def execute_rollback(record: dict[str, Any], guard: PathGuard, audit_log: JsonlAuditLog, rollback: RollbackStore, dry_run: bool = True, confirmed: bool = False) -> dict:
    operation = record.get("operation")
    rollback_payload = record.get("rollback") or {}
    if operation == "rename_file":
        source = rollback_payload.get("source")
        new_name = rollback_payload.get("new_name")
        if not source or not new_name:
            raise ValueError("Invalid rename rollback record")
        return rename_file(source, new_name, guard, audit_log, rollback, dry_run=dry_run, confirmed=confirmed) | {"rollback_executed": not dry_run}
    if operation == "move_file":
        source = rollback_payload.get("source")
        target = rollback_payload.get("target")
        if not source or not target:
            raise ValueError("Invalid move rollback record")
        return move_file(source, target, guard, audit_log, rollback, dry_run=dry_run, confirmed=confirmed) | {"rollback_executed": not dry_run}
    raise ValueError(f"Unsupported rollback operation: {operation}")


def execute_latest_rollback(guard: PathGuard, audit_log: JsonlAuditLog, rollback: RollbackStore, dry_run: bool = True, confirmed: bool = False) -> dict:
    records = rollback.read(1)
    if not records:
        return {"operation": "rollback", "dry_run": dry_run, "message": "No rollback records found"}
    return execute_rollback(records[-1], guard, audit_log, rollback, dry_run=dry_run, confirmed=confirmed)


def execute_operations_batch(
    operations: list[dict[str, Any]],
    guard: PathGuard,
    audit_log: JsonlAuditLog,
    rollback: RollbackStore,
    dry_run: bool = True,
    confirmed: bool = False,
    allow_delete: bool = False,
) -> dict:
    results = []
    for op in operations:
        name = op.get("operation")
        try:
            if name == "rename_file":
                result = rename_file(str(op["source"]), str(op["new_name"]), guard, audit_log, rollback, dry_run=dry_run, confirmed=confirmed)
            elif name == "move_file":
                result = move_file(str(op["source"]), str(op["target"]), guard, audit_log, rollback, dry_run=dry_run, confirmed=confirmed)
            elif name == "delete_file":
                result = delete_file(str(op["path"]), guard, audit_log, dry_run=dry_run, confirmed=confirmed, allow_delete=allow_delete)
            else:
                raise ValueError(f"Unsupported batch operation: {name}")
            results.append({"success": True, "operation": name, "result": result})
        except Exception as exc:
            results.append({"success": False, "operation": name, "error": str(exc), "input": op})
    return {
        "dry_run": dry_run,
        "confirmed": confirmed,
        "total": len(operations),
        "succeeded": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }


def build_file_organization_plan(path: str, allowed_extensions: list[str], guard: PathGuard, llm: BaseLLMClient, store: WorkspaceSQLiteStore | None = None) -> dict:
    scan = scan_folder(path, allowed_extensions, guard, store)
    items = []
    for item in scan["files"]:
        if item.get("error"):
            continue
        summary = ""
        if item["extension"] in DOC_EXTENSIONS | CODE_EXTENSIONS | IMAGE_EXTENSIONS:
            summary = llm.generate("summary", [{"text": read_document(item["path"]).get("text", "")}])
        suggestion = suggest_file_rename(item["path"])
        items.append({**item, "summary": summary, "suggested_name": suggestion["suggested_name"], "category": suggestion["category"]})
    if store:
        store.upsert_files(items)
    return {"root": scan["root"], "files": items, "duplicates": scan["duplicates"], "dry_run_operations": _make_operations(items)}


def _make_operations(items: list[dict]) -> list[dict]:
    ops = []
    for item in items:
        if item["filename"] != item["suggested_name"]:
            ops.append({"operation": "rename_file", "source": item["path"], "new_name": item["suggested_name"], "risk_level": "high", "requires_confirmation": True})
    return ops
