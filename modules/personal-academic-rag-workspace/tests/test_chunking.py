from __future__ import annotations

from pathlib import Path

from src.chunking.chunker import TextChunker
from src.ingestion.document_loader import load_document


def test_chunking_generates_chunk_id_and_source() -> None:
    segments = load_document(Path("examples/sample_docs/personal_knowledge.md"), collection="personal")
    chunks = TextChunker(chunk_size=180, chunk_overlap=20).chunk(segments)
    assert chunks
    assert chunks[0].chunk_id
    assert chunks[0].metadata["filename"] == "personal_knowledge.md"
    assert "source_path" in chunks[0].metadata

