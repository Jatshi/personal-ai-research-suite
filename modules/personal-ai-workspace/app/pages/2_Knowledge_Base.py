from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.tools.kb_tools import ingest_tool, list_docs_tool

config = load_config()
st.title("Knowledge Base")
path = st.text_input("Path", "./examples/sample_docs")
collection = st.text_input("Collection", "personal")
if st.button("Ingest"):
    st.json(ingest_tool(config, {"path": path, "collection": collection}))
st.dataframe(list_docs_tool(config, {"collection": collection})["documents"], use_container_width=True)

