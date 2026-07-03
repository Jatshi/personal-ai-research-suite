from __future__ import annotations

from pathlib import Path

from src.grounding.citation_builder import build_citations
from src.grounding.evidence_checker import has_sufficient_evidence
from src.indexing.index_manager import IndexManager


def test_citation_builder_and_evidence_checker(tmp_path: Path) -> None:
    from conftest import test_config

    manager = IndexManager(test_config(tmp_path))
    manager.ingest_path("examples/sample_docs", "personal")
    results = manager.search("RAG evidence citations", top_k=2)
    citations = build_citations(results)
    assert citations
    assert "chunk_id=" in citations[0]
    ok, conf = has_sufficient_evidence("RAG evidence citations", results, 0.1)
    assert ok
    assert conf > 0


def test_evidence_checker_rejects_empty() -> None:
    ok, conf = has_sufficient_evidence("unknown", [], 0.35)
    assert not ok
    assert conf == 0.0

