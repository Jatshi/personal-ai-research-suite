from __future__ import annotations

from src.indexing.bm25_store import BM25Store
from src.models import SearchResult


class KeywordRetriever:
    def __init__(self, bm25_store: BM25Store) -> None:
        self.bm25_store = bm25_store

    def search(self, query: str, top_k: int, filters: dict | None = None) -> list[SearchResult]:
        return self.bm25_store.search(query, top_k=top_k, filters=filters)

