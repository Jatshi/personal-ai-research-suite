from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config, resolve_project_path
from src.safety.audit_log import JsonlAuditLog
from src.tools.default_registry import build_registry


st.set_page_config(page_title="Personal Agent Workspace", layout="wide")
config = load_config(ROOT / "config.yaml")
registry = build_registry(config)
st.title("Personal Agent Workspace")
st.caption("Local AI agent system with tool calling, dry-run safety, human approval, logs, and workflows.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Workspace", str(resolve_project_path(config, config["app"]["workspace_dir"])))
c2.metric("Mock mode", str(config["app"]["mock_mode"]))
c3.metric("Tools", len(registry.specs()))
c4.metric("Agents", sum(1 for a in config["agents"].values() if a["enabled"]))

st.subheader("Enabled Agents")
st.json(config["agents"])

st.subheader("Recent Tool Calls")
log = JsonlAuditLog(resolve_project_path(config, config["logging"]["tool_log_file"]))
st.dataframe(log.read(20), use_container_width=True)

