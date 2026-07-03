from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry

st.title("Daily / Weekly Report")
registry = build_registry(load_config())
collection = st.text_input("Collection", "notes")
todo = st.text_input("Todo path in workspace", "todo.md")
if st.button("Generate Daily"):
    st.markdown(registry.call("generate_daily_report", {"collection": collection, "todo": todo})["report"])
if st.button("Generate Weekly"):
    st.markdown(registry.call("generate_weekly_report", {"collection": collection, "todo": todo})["report"])

