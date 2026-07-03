from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config, resolve_project_path
from src.safety.audit_log import JsonlAuditLog
from src.safety.rollback import RollbackStore
from src.storage.sqlite_store import WorkspaceSQLiteStore
from src.tools.default_registry import build_registry


st.title("Logs")
config = load_config(ROOT / "config.yaml")
registry = build_registry(config)
tool_log = JsonlAuditLog(resolve_project_path(config, config["logging"]["tool_log_file"]))
audit_log = JsonlAuditLog(resolve_project_path(config, config["logging"]["audit_log_file"]))
st.subheader("Tool Calls")
st.dataframe(tool_log.read(500), use_container_width=True)
st.subheader("File Operation Audit")
st.dataframe(audit_log.read(500), use_container_width=True)
st.subheader("Rollback Records")
rollback = RollbackStore(resolve_project_path(config, config["app"]["data_dir"]) / "logs" / "rollback.jsonl")
st.dataframe(rollback.read(500), use_container_width=True)
if st.button("Dry-run latest rollback"):
    st.json(registry.call("execute_latest_rollback", dry_run=True).__dict__)
confirm_rollback = st.checkbox("Confirm latest rollback execution")
if st.button("Execute latest rollback"):
    st.json(registry.call("execute_latest_rollback", dry_run=False, confirmed=confirm_rollback).__dict__)
st.subheader("File Inventory")
store = WorkspaceSQLiteStore(resolve_project_path(config, config["app"]["data_dir"]) / "indexes" / "agent_workspace.sqlite")
st.dataframe(store.list_files(500), use_container_width=True)
