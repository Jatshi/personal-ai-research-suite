from __future__ import annotations

from pathlib import Path

from src.indexing.bm25_store import BM25Store
from src.indexing.index_manager import IndexManager


def test_bm25_returns_keyword_document(tmp_path: Path) -> None:
    from conftest import test_config

    manager = IndexManager(test_config(tmp_path))
    manager.ingest_path("examples/sample_docs", "personal")
    chunks = manager.store.list_chunks()
    results = BM25Store(chunks).search("RAG citations", top_k=3)
    assert results
    assert "RAG" in results[0].chunk.text or "citations" in results[0].chunk.text


def test_semantic_and_hybrid_return_results(tmp_path: Path) -> None:
    from conftest import test_config

    manager = IndexManager(test_config(tmp_path))
    manager.ingest_path("examples/sample_docs", "personal")
    semantic = manager.search("resume project", mode="semantic", top_k=3)
    hybrid = manager.search("resume project", mode="hybrid", top_k=3)
    assert semantic
    assert hybrid

