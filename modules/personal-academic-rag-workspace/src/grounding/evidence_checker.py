from __future__ import annotations

from src.grounding.confidence import confidence_score
from src.models import SearchResult
from src.utils.text_utils import keyword_coverage


def has_sufficient_evidence(query: str, results: list[SearchResult], min_confidence: float = 0.35) -> tuple[bool, float]:
    conf = confidence_score(query, results)
    max_coverage = max((keyword_coverage(query, r.chunk.text) for r in results), default=0.0)
    max_score = max((max(r.score, r.rerank_score, r.vector_score, r.bm25_score) for r in results), default=0.0)
    return conf >= min_confidence and max_coverage >= 0.05 and max_score > 0.05, conf
