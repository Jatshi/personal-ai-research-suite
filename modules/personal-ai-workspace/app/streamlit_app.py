from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.storage.sqlite_store import SQLiteStore

st.set_page_config(page_title="Personal AI Workspace", layout="wide")
config = load_config()
store = SQLiteStore(config)

st.title("Personal AI Workspace")
st.caption("Local-first Personal AI OS prototype: KB, RAG, Agent tools, MCP-like tools, evaluation, reports, reading RAG, observability, safety.")

cols = st.columns(4)
cols[0].metric("Documents", store.count_documents())
cols[1].metric("Mock Mode", str(config["app"]["mock_mode"]))
cols[2].metric("Retrieval", config["retrieval"]["default_mode"])
cols[3].metric("Workspace", config["app"]["workspace_dir"])

st.subheader("Quick Start")
st.code(
    "python -m src.cli ingest --path ./examples/sample_docs --collection personal\n"
    "python -m src.cli search --query \"RAG 是什么？\" --mode hybrid --top-k 5\n"
    "python -m src.cli ask --query \"请总结这个知识库中的主要主题。\" --collection personal",
    language="bash",
)

st.subheader("Recent Documents")
st.dataframe(store.list_documents()[:20], use_container_width=True)

