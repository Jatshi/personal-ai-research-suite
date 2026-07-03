from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.indexing.index_manager import IndexManager


st.title("Ask")
manager = IndexManager(load_config(ROOT / "config.yaml"))
query = st.text_area("Question", "请总结示例论文的方法。")
collection = st.selectbox("Collection", ["", "personal", "academic"])
mode = st.selectbox("Retrieval mode", ["hybrid", "keyword", "semantic"])
top_k = st.slider("Top K", 1, 12, 5)

if st.button("Generate answer", type="primary"):
    answer = manager.ask(query, collection or None, mode, top_k)
    st.subheader("Answer")
    st.write(answer.text)
    st.progress(answer.confidence)
    st.caption(f"confidence={answer.confidence:.3f}")
    st.subheader("Evidence")
    for r in answer.evidence:
        with st.expander(f"{r.chunk.metadata.get('filename')} | {r.chunk.chunk_id} | score={r.score:.3f}"):
            st.write(r.chunk.text)

