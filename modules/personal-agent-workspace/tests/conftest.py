from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def cfg(tmp_path: Path) -> dict:
    workspace = ROOT / "workspace" / "test_runs" / tmp_path.name
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    shutil.copytree(ROOT / "examples" / "messy_files", workspace / "messy_files")
    shutil.copytree(ROOT / "examples" / "papers", workspace / "papers")
    shutil.copytree(ROOT / "examples" / "thesis_sample", workspace / "thesis_sample")
    shutil.copy2(ROOT / "examples" / "todo.md", workspace / "todo.md")
    return {
        "_project_root": str(ROOT),
        "app": {"name": "test", "workspace_dir": str(workspace), "data_dir": str(workspace / "data"), "mock_mode": True},
        "llm": {"backend": "mock", "model_name": "mock", "temperature": 0.2, "max_tokens": 1200},
        "agents": {"file_organizer": {"enabled": True}, "thesis_finishing": {"enabled": True}, "paper_reading": {"enabled": True}, "work_assistant": {"enabled": True}},
        "safety": {"require_confirmation_for_write": True, "enable_dry_run": True, "allow_delete": False, "block_hidden_files": True, "block_env_files": True, "allow_paths_outside_workspace": False},
        "file_organizer": {"allowed_extensions": [".md", ".txt", ".py"], "duplicate_check": {"use_hash": True, "use_filename_similarity": True}},
        "thesis": {"export_markdown": True, "export_json": True},
        "paper_reading": {"output_dir": str(workspace / "data" / "exports" / "paper_notes"), "use_multi_agent": True},
        "logging": {"level": "INFO", "log_dir": str(workspace / "data" / "logs"), "tool_log_file": str(workspace / "data" / "logs" / "tool_calls.jsonl"), "audit_log_file": str(workspace / "data" / "logs" / "audit_log.jsonl")},
    }

