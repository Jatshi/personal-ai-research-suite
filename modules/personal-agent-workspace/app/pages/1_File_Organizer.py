from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


st.title("File Organizer Agent")
registry = build_registry(load_config(ROOT / "config.yaml"))
path = st.text_input("Workspace-relative path", "messy_files")

if st.button("Scan files"):
    result = registry.call("scan_folder", {"path": path}).output
    st.session_state["scan"] = result
if st.button("Generate dry-run organization plan"):
    result = registry.call("organize_files", {"path": path}, dry_run=True).output
    st.session_state["plan"] = result

if "scan" in st.session_state:
    st.subheader("File Manifest")
    st.dataframe(st.session_state["scan"]["files"], use_container_width=True)
    st.subheader("Duplicates")
    st.json(st.session_state["scan"]["duplicates"])

if "plan" in st.session_state:
    st.subheader("Summaries and Suggestions")
    st.dataframe(st.session_state["plan"]["files"], use_container_width=True)
    st.subheader("Dry-run Operations")
    ops = st.session_state["plan"]["dry_run_operations"]
    st.json(ops)
    st.caption("Batch execution is high risk. Run a dry-run first; real execution requires explicit confirmation.")
    if st.button("Dry-run batch operations"):
        res = registry.call("execute_operations_batch", {"operations": ops}, dry_run=True)
        st.json(res.__dict__)
    batch_confirm = st.checkbox("Confirm batch execution")
    if st.button("Execute confirmed batch operations"):
        res = registry.call("execute_operations_batch", {"operations": ops}, confirmed=batch_confirm, dry_run=False)
        st.json(res.__dict__)
    for i, op in enumerate(ops):
        with st.expander(f"{op['operation']} {Path(op['source']).name}"):
            st.json(op)
            if st.checkbox("Confirm this operation", key=f"confirm_{i}"):
                if st.button("Execute rename", key=f"exec_{i}"):
                    res = registry.call("rename_file", {"source": op["source"], "new_name": op["new_name"]}, confirmed=True, dry_run=False)
                    st.json(res.__dict__)
