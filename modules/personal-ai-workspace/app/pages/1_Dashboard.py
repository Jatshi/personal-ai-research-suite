from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.observability.trace_logger import JsonlLogger
from src.storage.sqlite_store import SQLiteStore

config = load_config()
store = SQLiteStore(config)
st.title("Dashboard")
st.metric("Knowledge base documents", store.count_documents())
st.subheader("Recent RAG Queries")
st.json(JsonlLogger(config, "rag_queries.jsonl").tail(10))
st.subheader("Recent Tool Calls")
st.json(JsonlLogger(config, "tool_calls.jsonl").tail(10))

