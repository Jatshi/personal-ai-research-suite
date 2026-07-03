from __future__ import annotations

from typing import Any

from src.utils.text_utils import tokenize


NO_EVIDENCE = "知识库中没有足够证据回答该问题。"


def confidence_score(query: str, chunks: list[dict[str, Any]]) -> float:
    if not chunks:
        return 0.0
    terms = set(tokenize(query))
    coverages = [len(terms & set(tokenize(c.get("text", "")))) / max(len(terms), 1) for c in chunks]
    top_score = max(c.get("score", 0.0) for c in chunks)
    summary_bonus = 0.12 if top_score > 0.05 and any(word in query for word in ["总结", "主题", "概括", "overview"]) else 0.0
    return round(min(1.0, 0.45 * top_score + 0.35 * max(coverages) + 0.2 * min(len(chunks), 5) / 5 + summary_bonus), 3)


def has_enough_evidence(query: str, chunks: list[dict[str, Any]], min_confidence: float) -> tuple[bool, float]:
    confidence = confidence_score(query, chunks)
    return confidence >= min_confidence, confidence
