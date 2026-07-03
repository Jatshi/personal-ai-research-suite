from __future__ import annotations

from src.models import SearchResult
from src.utils.text_utils import keyword_coverage, tokenize


class RuleReranker:
    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        q_terms = set(tokenize(query))
        for r in results:
            meta_text = f"{r.chunk.metadata.get('filename','')} {r.chunk.metadata.get('heading','')}"
            title_hit = 1.0 if q_terms & set(tokenize(meta_text)) else 0.0
            coverage = keyword_coverage(query, r.chunk.text)
            base = max(r.score, r.bm25_score, r.vector_score)
            r.rerank_score = round(0.55 * base + 0.30 * coverage + 0.15 * title_hit, 4)
            r.score = r.rerank_score
            r.debug["keyword_coverage"] = coverage
            r.debug["title_hit"] = title_hit
        return sorted(results, key=lambda x: x.rerank_score, reverse=True)[:top_k]

