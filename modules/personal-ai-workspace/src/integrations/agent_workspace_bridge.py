from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any


_PENDING_ORGANIZE_PLANS: dict[str, dict[str, Any]] = {}


def run_file_organizer(config: dict[str, Any], path: str) -> dict[str, Any]:
    response = _run_agent_cli(config, "organize-files", path)
    operations = response.get("result", {}).get("dry_run_operations", [])
    token = uuid.uuid4().hex
    _PENDING_ORGANIZE_PLANS[token] = {
        "path": response["path"],
        "operations_hash": _operations_hash(operations),
        "expires_at": time.time() + 900,
    }
    return {**response, "approval_token": token, "approval_expires_in_seconds": 900}


def execute_file_organizer(config: dict[str, Any], path: str, approval_token: str) -> dict[str, Any]:
    root = _agent_workspace_root(config)
    relative_path = _safe_relative_path(path)
    pending = _PENDING_ORGANIZE_PLANS.pop(approval_token, None)
    if not pending or pending["path"] != relative_path or pending["expires_at"] < time.time():
        raise ValueError("The approval token is missing, expired, or does not match this dry-run plan.")
    current = _run_agent_cli(config, "organize-files", relative_path)
    if _operations_hash(current.get("result", {}).get("dry_run_operations", [])) != pending["operations_hash"]:
        raise ValueError("The file plan changed after preview. Review a new dry-run plan before execution.")
    completed = subprocess.run(
        [sys.executable, "-m", "src.cli", "execute-organize-plan", "--path", relative_path, "--execute", "--yes"],
        cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True,
        timeout=int(config.get("integrations", {}).get("agent_workspace_timeout_seconds", 120)), check=False,
    )
    if completed.returncode:
        raise RuntimeError(_safe_error(completed.stderr or completed.stdout))
    return {"success": True, "module": "personal-agent-workspace", "command": "execute-organize-plan", "path": relative_path, "executed": True, "result": _parse_cli_json(completed.stdout)}


def run_thesis_check(config: dict[str, Any], path: str) -> dict[str, Any]:
    response = _run_agent_cli(config, "check-thesis", path)
    report_path = _agent_workspace_root(config) / "data" / "exports" / "thesis_check_report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Thesis check completed but its structured JSON report could not be read.") from exc
    return {**response, "report": report}


def run_paper_reading(config: dict[str, Any], path: str) -> dict[str, Any]:
    root = _agent_workspace_root(config)
    relative_path = _safe_relative_path(path)
    output = "./data/exports/web-paper-notes"
    completed = subprocess.run(
        [sys.executable, "-m", "src.cli", "read-papers", "--path", relative_path, "--output", output],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=int(config.get("integrations", {}).get("agent_workspace_timeout_seconds", 120)),
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(_safe_error(completed.stderr or completed.stdout))
    workflow_path = root / "data" / "exports" / "web-paper-notes" / "workflow_log.json"
    try:
        workflow = _public_workflow(json.loads(workflow_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Paper reading completed but its workflow log could not be read.") from exc
    return {
        "success": True,
        "module": "personal-agent-workspace",
        "command": "read-papers",
        "path": relative_path,
        "output": output,
        "result": _parse_cli_json(completed.stdout),
        "workflow": workflow,
    }


def run_mcp_doctor(config: dict[str, Any]) -> dict[str, Any]:
    root = _sibling_root(config, "mcp_toolkit_root", "../local-mcp-toolkit")
    completed = subprocess.run(
        [sys.executable, "-m", "src.cli", "doctor-mcp"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=int(config.get("integrations", {}).get("mcp_toolkit_timeout_seconds", 60)),
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(_safe_error(completed.stderr or completed.stdout))
    return {"success": True, "module": "local-mcp-toolkit", "result": _parse_cli_json(completed.stdout)}


def _run_agent_cli(config: dict[str, Any], command: str, path: str) -> dict[str, Any]:
    root = _agent_workspace_root(config)
    relative_path = _safe_relative_path(path)
    # The sibling module validates the path again with its own PathGuard. This bridge
    # only exposes read-only commands; it never passes --execute or --yes.
    completed = subprocess.run(
        [sys.executable, "-m", "src.cli", command, "--path", relative_path],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=int(config.get("integrations", {}).get("agent_workspace_timeout_seconds", 120)),
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(_safe_error(completed.stderr or completed.stdout))
    return {
        "success": True,
        "module": "personal-agent-workspace",
        "command": command,
        "path": relative_path,
        "dry_run": command == "organize-files",
        "result": _parse_cli_json(completed.stdout),
    }


def _agent_workspace_root(config: dict[str, Any]) -> Path:
    root = _sibling_root(config, "agent_workspace_root", "../personal-agent-workspace")
    if not (root / "src" / "cli.py").exists():
        raise RuntimeError(f"Personal Agent Workspace is unavailable: {root}")
    return root


def _sibling_root(config: dict[str, Any], key: str, default: str) -> Path:
    configured = config.get("integrations", {}).get(key)
    project_root = Path(config["_project_root"])
    candidate = Path(configured) if configured else Path(default)
    return candidate.resolve() if candidate.is_absolute() else (project_root / candidate).resolve()


def _safe_relative_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts or not str(candidate).strip():
        raise ValueError("Use a non-empty path below personal-agent-workspace/workspace/.")
    if not candidate.parts or candidate.parts[0].lower() != "workspace":
        raise ValueError("Bridge paths must start with workspace/.")
    return candidate.as_posix()


def _parse_cli_json(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Some existing CLI commands include human-readable report paths before their
        # final JSON line. Preserve stdout rather than pretending it is structured.
        for line in reversed(text.splitlines()):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {"stdout": text}


def _safe_error(value: str) -> str:
    return value.strip()[-2000:] or "The Personal Agent Workspace command failed."


def _operations_hash(operations: list[dict[str, Any]]) -> str:
    payload = json.dumps(operations, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _public_workflow(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    public: list[dict[str, Any]] = []
    for entry in entries:
        steps = entry.get("steps", {}) if isinstance(entry.get("steps"), dict) else {}
        reader = steps.get("reader", {}) if isinstance(steps.get("reader"), dict) else {}
        public.append({
            "file_name": Path(str(entry.get("file", ""))).name,
            "status": entry.get("status", "unknown"),
            "title": reader.get("title", "Untitled paper"),
            "year": reader.get("year"),
            "completed_roles": [name for name in ("reader", "method", "experiment", "critic", "writer") if name in steps],
            "error_count": len(entry.get("errors", [])) if isinstance(entry.get("errors"), list) else 0,
        })
    return public
