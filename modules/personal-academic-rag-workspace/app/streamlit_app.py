from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.indexing.index_manager import IndexManager


st.set_page_config(page_title="Academic RAG Workspace", layout="wide")
st.title("Personal Academic RAG Workspace")
st.caption("Local-first RAG for personal documents, papers, notes, and doctoral materials.")

config = load_config(ROOT / "config.yaml")
manager = IndexManager(config)

docs = manager.store.list_documents()
papers = manager.store.list_papers()
chunks = manager.store.list_chunks()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Documents", len(docs))
c2.metric("Chunks", len(chunks))
c3.metric("Papers", len(papers))
c4.metric("Vector backend", manager.vector_store.backend)

st.subheader("Quick Ask")
query = st.text_input("Question", "这个知识库里有哪些研究主题？")
collection = st.selectbox("Collection", ["", "personal", "academic"])
if st.button("Ask", type="primary"):
    answer = manager.ask(query, collection or None)
    st.write(answer.text)
    st.progress(answer.confidence)
    st.caption(f"confidence={answer.confidence:.3f}")
    for r in answer.evidence:
        with st.expander(f"{r.chunk.metadata.get('filename')} | score={r.score:.3f} | {r.chunk.chunk_id}"):
            st.write(r.chunk.text)

