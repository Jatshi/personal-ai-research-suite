from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.grounding.evidence_checker import confidence_score


@dataclass(frozen=True)
class RouteDecision:
    route: str
    confidence: float
    reason: str


def decide_route(query: str, chunks: list[dict[str, Any]], min_confidence: float) -> RouteDecision:
    confidence = confidence_score(query, chunks)
    if not chunks or confidence < min_confidence:
        return RouteDecision("low", confidence, "insufficient_evidence")
    if confidence < min(0.75, min_confidence + 0.25):
        return RouteDecision("medium", confidence, "expand_retrieval")
    return RouteDecision("high", confidence, "direct_answer")
