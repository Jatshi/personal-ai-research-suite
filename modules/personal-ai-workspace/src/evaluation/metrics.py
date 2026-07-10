from __future__ import annotations

from typing import Any


def compute_rag_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    total = len(records) or 1
    return {
        "retrieval_hit_rate": sum(bool(r.get("source_hit")) for r in records) / total,
        "source_accuracy": sum(bool(r.get("source_hit")) for r in records) / total,
        "citation_presence": sum(bool(r.get("citations")) for r in records if r.get("should_answer", True)) / max(sum(bool(r.get("should_answer", True)) for r in records), 1),
        "refusal_accuracy": sum(bool(r.get("refused")) == (not r.get("should_answer", True)) for r in records) / total,
        "answer_keyword_coverage": sum(float(r.get("keyword_coverage", 0.0)) for r in records) / total,
        "average_confidence": sum(float(r.get("confidence", 0.0)) for r in records) / total,
        "route_accuracy": sum(r.get("expected_route") is None or r.get("expected_route") == r.get("actual_route") for r in records) / total,
        "context_compression_ratio": sum(float(r.get("compression_ratio", 1.0)) for r in records) / total,
        "citation_retention": sum(bool(r.get("citation_retained", True)) for r in records) / total,
    }
