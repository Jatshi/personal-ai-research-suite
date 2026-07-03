from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.observability.trace_logger import JsonlLogger

config = load_config()
st.title("Observability")
for name in ["rag_queries.jsonl", "tool_calls.jsonl", "llm_calls.jsonl", "audit_log.jsonl", "errors.jsonl"]:
    st.subheader(name)
    st.json(JsonlLogger(config, name).tail(50))

