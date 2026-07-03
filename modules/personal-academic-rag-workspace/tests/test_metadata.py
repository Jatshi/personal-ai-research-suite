from __future__ import annotations

from pathlib import Path

from src.ingestion.document_loader import load_document
from src.storage.metadata_store import MetadataStore


def test_markdown_loader_returns_text_and_metadata() -> None:
    path = Path("examples/sample_docs/personal_knowledge.md")
    segments = load_document(path, collection="personal")
    assert segments
    assert segments[0].text
    assert segments[0].metadata["filename"] == "personal_knowledge.md"
    assert segments[0].metadata["collection"] == "personal"


def test_metadata_store_roundtrip(tmp_path: Path) -> None:
    store = MetadataStore(tmp_path / "rag.sqlite")
    docs = store.list_documents()
    assert docs == []

