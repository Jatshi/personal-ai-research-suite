from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_file_organizer(config: dict[str, Any], path: str) -> dict[str, Any]:
    return _run_agent_cli(config, "organize-files", path)


def run_thesis_check(config: dict[str, Any], path: str) -> dict[str, Any]:
    return _run_agent_cli(config, "check-thesis", path)


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
    configured = config.get("integrations", {}).get("agent_workspace_root")
    root = Path(configured).resolve() if configured else Path(config["_project_root"]).parent / "personal-agent-workspace"
    if not (root / "src" / "cli.py").exists():
        raise RuntimeError(f"Personal Agent Workspace is unavailable: {root}")
    return root


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
