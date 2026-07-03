from src.retrieval.hybrid_retriever import search_chunks


def test_hybrid_search_returns_keyword_hit():
    chunks = [{"chunk_id": "1", "text": "RAG uses retrieval and generation", "embedding": [1.0, 0.0]}]
    out = search_chunks(chunks, "RAG retrieval", mode="keyword", top_k=1)
    assert out and out[0]["chunk_id"] == "1"


def test_hybrid_search_accepts_external_semantic_results():
    chunks = [{"chunk_id": "keyword", "text": "plain keyword match", "embedding": [1.0, 0.0]}]
    semantic = [{"chunk_id": "semantic", "text": "semantic evidence", "vector_score": 0.95, "score": 0.95}]
    out = search_chunks(chunks, "semantic", mode="hybrid", top_k=2, semantic_results=semantic)
    ids = {item["chunk_id"] for item in out}
    assert "semantic" in ids
