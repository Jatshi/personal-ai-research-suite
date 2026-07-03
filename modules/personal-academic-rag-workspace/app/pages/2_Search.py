from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.indexing.index_manager import IndexManager
from src.utils.highlighting import highlight_keywords


st.title("Search")
manager = IndexManager(load_config(ROOT / "config.yaml"))

query = st.text_input("Query", "请总结文档中关于 RAG 的内容。")
mode = st.radio("Mode", ["hybrid", "keyword", "semantic"], horizontal=True)
top_k = st.slider("Top K", 1, 20, 5)
c1, c2, c3 = st.columns(3)
collection = c1.text_input("Collection filter", "")
tags = c2.text_input("Tags filter comma separated", "")
doc_type = c3.text_input("Doc type filter", "")

if st.button("Search", type="primary"):
    filters = {}
    if collection:
        filters["collection"] = collection
    if doc_type:
        filters["doc_type"] = doc_type
    if tags:
        filters["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    results = manager.search(query, mode, top_k, filters)
    for i, r in enumerate(results, start=1):
        st.markdown(f"### {i}. {r.chunk.metadata.get('filename')} | score={r.score:.3f}")
        st.caption(f"chunk_id={r.chunk.chunk_id} bm25={r.bm25_score:.3f} vector={r.vector_score:.3f} rerank={r.rerank_score:.3f}")
        st.markdown(highlight_keywords(r.chunk.text[:1200], query), unsafe_allow_html=True)

