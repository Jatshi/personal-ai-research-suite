from __future__ import annotations

import math
from typing import Any


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / ((math.sqrt(sum(x * x for x in a)) or 1.0) * (math.sqrt(sum(y * y for y in b)) or 1.0))


def vector_search(chunks: list[dict[str, Any]], query_embedding: list[float], top_k: int) -> list[dict[str, Any]]:
    scored = []
    for chunk in chunks:
        score = cosine(chunk.get("embedding", []), query_embedding)
        item = dict(chunk)
        item["vector_score"] = score
        item["score"] = score
        scored.append(item)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

