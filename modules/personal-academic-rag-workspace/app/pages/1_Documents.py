from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.indexing.index_manager import IndexManager


st.title("Documents")
manager = IndexManager(load_config(ROOT / "config.yaml"))

with st.form("upload"):
    files = st.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "docx", "pptx", "md", "txt"])
    collection = st.text_input("Collection", "personal")
    tags = st.text_input("Tags comma separated", "")
    doc_type = st.text_input("Doc type", "general")
    submitted = st.form_submit_button("Import")
    if submitted and files:
        tmp = ROOT / "data" / "uploads"
        tmp.mkdir(parents=True, exist_ok=True)
        for f in files:
            path = tmp / f.name
            path.write_bytes(f.getbuffer())
            manager.ingest_path(path, collection, [x.strip() for x in tags.split(",") if x.strip()], doc_type)
        st.success(f"Imported {len(files)} file(s)")

with st.form("folder"):
    folder = st.text_input("Batch import folder")
    folder_collection = st.text_input("Folder collection", "academic")
    if st.form_submit_button("Import folder") and folder:
        ids = manager.ingest_path(folder, folder_collection, doc_type="paper" if folder_collection == "academic" else "general")
        st.success(f"Imported {len(ids)} document(s)")

docs = manager.store.list_documents()
st.subheader("Imported Documents")
for doc in docs:
    with st.expander(f"{doc['filename']} | {doc['collection']} | {doc['doc_id']}"):
        st.json(doc)
        confirm = st.checkbox(f"Confirm delete {doc['doc_id']}", key=f"confirm_{doc['doc_id']}")
        if st.button("Delete document", key=f"delete_{doc['doc_id']}", disabled=not confirm):
            count = manager.delete_document(doc["doc_id"])
            st.warning(f"Deleted {count} chunks. Refresh page to update list.")

if st.button("Reindex all"):
    st.success(f"Reindexed {manager.reindex()} chunks")

