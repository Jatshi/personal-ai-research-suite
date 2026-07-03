from src.config.config_loader import load_config
from src.ingestion.document_loader import load_document


def test_document_loader_md_returns_text_and_metadata():
    doc = load_document("examples/sample_docs/rag_intro.md")
    assert "RAG" in doc["text"]
    assert doc["metadata"]["title"]

