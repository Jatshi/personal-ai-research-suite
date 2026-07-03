from __future__ import annotations

from src.models import SearchResult
from src.retrieval.keyword_retriever import KeywordRetriever
from src.retrieval.reranker import RuleReranker
from src.retrieval.semantic_retriever import SemanticRetriever


class HybridRetriever:
    def __init__(
        self,
        keyword_retriever: KeywordRetriever,
        semantic_retriever: SemanticRetriever,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        reranker: RuleReranker | None = None,
    ) -> None:
        self.keyword_retriever = keyword_retriever
        self.semantic_retriever = semantic_retriever
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.reranker = reranker or RuleReranker()

    def search(self, query: str, top_k: int, mode: str = "hybrid", filters: dict | None = None) -> list[SearchResult]:
        if mode == "keyword":
            return self.reranker.rerank(query, self.keyword_retriever.search(query, top_k, filters), top_k)
        if mode == "semantic":
            return self.reranker.rerank(query, self.semantic_retriever.search(query, top_k, filters), top_k)
        k = max(top_k * 3, 10)
        merged: dict[str, SearchResult] = {}
        for r in self.keyword_retriever.search(query, k, filters):
            merged[r.chunk.chunk_id] = r
        for r in self.semantic_retriever.search(query, k, filters):
            if r.chunk.chunk_id in merged:
                merged[r.chunk.chunk_id].vector_score = r.vector_score
            else:
                merged[r.chunk.chunk_id] = r
        for r in merged.values():
            r.score = self.bm25_weight * r.bm25_score + self.vector_weight * r.vector_score
        return self.reranker.rerank(query, list(merged.values()), top_k)

