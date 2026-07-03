from __future__ import annotations

from src.models import SearchResult
from src.utils.text_utils import keyword_coverage


def confidence_score(query: str, results: list[SearchResult]) -> float:
    if not results:
        return 0.0
    top = max(results[0].score, results[0].rerank_score, results[0].vector_score, results[0].bm25_score)
    count_factor = min(len(results) / 5, 1.0)
    coverage = max(keyword_coverage(query, r.chunk.text) for r in results)
    if coverage <= 0:
        return round(min(0.2, 0.45 * min(top, 1.0)), 3)
    score = 0.45 * min(top, 1.0) + 0.25 * count_factor + 0.30 * coverage
    return round(max(0.0, min(score, 1.0)), 3)
