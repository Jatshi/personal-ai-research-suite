from src.grounding.citation_builder import build_citations
from src.grounding.evidence_checker import has_enough_evidence


def test_citation_and_refusal():
    chunks = [{"file_name": "a.md", "paragraph_number": 1, "chunk_id": "c1", "text": "RAG retrieval", "score": 0.8}]
    assert "chunk_id=c1" in build_citations(chunks)[0]
    ok, _ = has_enough_evidence("unrelated mars budget", [], 0.3)
    assert not ok

