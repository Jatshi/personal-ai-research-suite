from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.academic.literature_table import LiteratureTableGenerator
from src.academic.paper_comparator import PaperComparator
from src.academic.paper_note_generator import PaperNoteGenerator
from src.config.config_loader import load_config
from src.indexing.index_manager import IndexManager


st.title("Academic")
manager = IndexManager(load_config(ROOT / "config.yaml"))
papers = manager.store.list_papers()
st.caption(f"{len(papers)} paper(s)")

if papers:
    titles = [p.get("title") or p.get("filename") for p in papers]
    selected = st.selectbox("Paper", titles)
    paper = papers[titles.index(selected)]
    st.json({k: v for k, v in paper.items() if k != "sections"})
    chunks = manager.store.get_chunks_by_doc(paper["doc_id"])
    if st.button("Generate reading note"):
        note = PaperNoteGenerator().generate(paper, paper.get("sections", {}), chunks)
        st.download_button("Download note", note, file_name="paper_note.md")
        st.markdown(note)
    if st.button("Generate comparison"):
        comp = PaperComparator().compare(papers)
        st.markdown(comp)
    if st.button("Generate literature table"):
        table = LiteratureTableGenerator().generate(papers)
        st.download_button("Download table", table, file_name="literature_table.md")
        st.markdown(table)
else:
    st.info("Import academic documents first.")

