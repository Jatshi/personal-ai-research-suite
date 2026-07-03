from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.reading.article_extractor import import_reading_path
from src.reading.reading_tools import reading_list_markdown, reading_search

config = load_config()
st.title("Reading RAG")
path = st.text_input("Reading path", "./examples/sample_reading")
if st.button("Import Reading"):
    st.json(import_reading_path(config, path, "reading"))
query = st.text_input("Search reading", "Agent Harness")
if st.button("Search Reading"):
    st.json(reading_search(config, query))
topic = st.text_input("Topic", "AI Agent 安全")
if st.button("Generate Reading List"):
    st.markdown(reading_list_markdown(config, topic))

