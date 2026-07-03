from __future__ import annotations

import json

import streamlit as st

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry

registry = build_registry(load_config())
st.title("MCP Tools")
st.json(registry.list_tools())
tool = st.text_input("Tool", "search_kb")
args = st.text_area("Args JSON", '{"query":"RAG 是什么？"}')
if st.button("Call Tool"):
    st.json(registry.call(tool, json.loads(args)))

