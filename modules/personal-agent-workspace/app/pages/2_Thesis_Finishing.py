from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


st.title("Thesis Finishing Agent")
registry = build_registry(load_config(ROOT / "config.yaml"))
path = st.text_input("Thesis path", "thesis_sample/thesis.md")
if st.button("Run thesis check"):
    result = registry.call("check_thesis", {"path": path}).output
    st.session_state["thesis_report"] = result

if "thesis_report" in st.session_state:
    report = st.session_state["thesis_report"]
    st.subheader("Todos")
    st.dataframe(report["todos"], use_container_width=True)
    st.subheader("Structure")
    st.json(report["structure"])
    st.subheader("Figures / Tables / Equations")
    st.json(report["figures_tables_equations"])
    st.subheader("Bibliography")
    st.json(report["bibliography"])

