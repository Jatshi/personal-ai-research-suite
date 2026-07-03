from __future__ import annotations

from typing import Any

from src.generation.embedding_client import BaseEmbeddingClient
from src.generation.mock_embedding import MockEmbeddingClient
from src.indexing.bm25_store import bm25_search
from src.indexing.vector_store import vector_search
from src.utils.text_utils import tokenize


def search_chunks(
    chunks: list[dict[str, Any]],
    query: str,
    mode: str = "hybrid",
    top_k: int = 5,
    bm25_weight: float = 0.4,
    vector_weight: float = 0.6,
    embedding_dim: int = 384,
    embedder: BaseEmbeddingClient | None = None,
    semantic_results: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if mode == "keyword":
        return bm25_search(chunks, query, top_k)
    if semantic_results is None:
        active_embedder = embedder or MockEmbeddingClient(embedding_dim)
        sem = vector_search(chunks, active_embedder.embed_query(query), top_k * 2)
    else:
        sem = semantic_results[: top_k * 2]
    if mode == "semantic":
        return sem[:top_k]
    key = bm25_search(chunks, query, top_k * 2)
    merged: dict[str, dict[str, Any]] = {}
    max_b = max([x.get("bm25_score", 0.0) for x in key] + [1.0])
    max_v = max([x.get("vector_score", 0.0) for x in sem] + [1.0])
    for item in key + sem:
        cid = item["chunk_id"]
        existing = merged.setdefault(cid, dict(item))
        existing["bm25_score"] = max(existing.get("bm25_score", 0.0), item.get("bm25_score", 0.0))
        existing["vector_score"] = max(existing.get("vector_score", 0.0), item.get("vector_score", 0.0))
    query_terms = set(tokenize(query))
    for item in merged.values():
        coverage = len(query_terms & set(tokenize(item.get("text", "")))) / max(len(query_terms), 1)
        item["score"] = bm25_weight * (item.get("bm25_score", 0.0) / max_b) + vector_weight * (item.get("vector_score", 0.0) / max_v) + 0.1 * coverage
    return sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:top_k]
