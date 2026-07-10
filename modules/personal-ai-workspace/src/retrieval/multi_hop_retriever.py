from __future__ import annotations

import re
from typing import Any, Callable


def expand_query_from_results(query: str, chunks: list[dict[str, Any]]) -> str | None:
    words: list[str] = []
    for chunk in chunks[:3]:
        words.extend(re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", chunk.get("text", "")))
    unique = [word for word in dict.fromkeys(words) if word.lower() not in query.lower()]
    return f"{query} {' '.join(unique[:3])}" if unique else None


def retrieve_multi_hop(
    query: str,
    initial: list[dict[str, Any]],
    search: Callable[[str, int], list[dict[str, Any]]],
    max_hops: int,
    top_k: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    merged = {item["chunk_id"]: {**item, "hop": 1, "query_variant": query} for item in initial}
    trace = [{"hop": 1, "query": query, "result_count": len(initial)}]
    current = initial
    for hop in range(2, max_hops + 1):
        expanded = expand_query_from_results(query, current)
        if not expanded:
            break
        current = search(expanded, top_k)
        trace.append({"hop": hop, "query": expanded, "result_count": len(current)})
        for item in current:
            merged.setdefault(item["chunk_id"], {**item, "hop": hop, "query_variant": expanded})
    return sorted(merged.values(), key=lambda item: item.get("score", 0.0), reverse=True)[:top_k], trace
