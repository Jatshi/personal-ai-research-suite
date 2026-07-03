from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


st.title("Paper Reading Multi-Agent Workflow")
registry = build_registry(load_config(ROOT / "config.yaml"))
path = st.text_input("Papers path", "papers")
output = st.text_input("Output path", "./data/exports/paper_notes")
if st.button("Run paper workflow"):
    result = registry.call("read_papers", {"path": path, "output": output}).output
    st.session_state["paper_result"] = result

if "paper_result" in st.session_state:
    result = st.session_state["paper_result"]
    st.success(f"Generated notes in {result['output_dir']}")
    st.markdown(result["table"])
    st.subheader("Workflow Log")
    st.json(result["log"])

