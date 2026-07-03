from __future__ import annotations

from pathlib import Path

from src.academic.paper_metadata_extractor import PaperMetadataExtractor
from src.academic.paper_note_generator import PaperNoteGenerator
from src.academic.section_parser import SectionParser
from src.indexing.index_manager import IndexManager


def test_academic_metadata_and_note(tmp_path: Path) -> None:
    from conftest import test_config

    manager = IndexManager(test_config(tmp_path))
    ids = manager.ingest_path("examples/sample_papers", "academic", doc_type="paper")
    assert ids
    chunks = manager.store.get_chunks_by_doc(ids[0])
    metadata = PaperMetadataExtractor().extract(chunks)
    sections = SectionParser().parse(chunks)
    note = PaperNoteGenerator().generate(metadata, sections, chunks)
    assert metadata["title"]
    assert "Paper Reading Note" in note
    assert "Key Evidence" in note

