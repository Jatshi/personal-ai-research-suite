from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry

config = load_config()
registry = build_registry(config)
st.title("Search and Ask")
query = st.text_input("Query", "RAG 是什么？")
collection = st.text_input("Collection", "personal")
mode = st.selectbox("Mode", ["hybrid", "keyword", "semantic"])
top_k = st.slider("Top K", 1, 10, 5)
if st.button("Search"):
    st.json(registry.call("search_kb", {"query": query, "collection": collection, "mode": mode, "top_k": top_k}))
if st.button("Ask"):
    result = registry.call("ask_kb", {"query": query, "collection": collection, "mode": mode, "top_k": top_k})
    st.markdown(result.get("answer", ""))
    st.metric("Confidence", result.get("confidence", 0))
    st.write(result.get("citations", []))

