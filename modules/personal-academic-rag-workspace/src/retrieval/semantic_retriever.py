from __future__ import annotations

from src.indexing.vector_store import VectorStore
from src.models import SearchResult


class SemanticRetriever:
    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def search(self, query: str, top_k: int, filters: dict | None = None) -> list[SearchResult]:
        return self.vector_store.search(query, top_k=top_k, filters=filters)

