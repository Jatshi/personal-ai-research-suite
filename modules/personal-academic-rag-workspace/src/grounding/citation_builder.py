from __future__ import annotations

from src.models import SearchResult


def build_citations(results: list[SearchResult]) -> list[str]:
    citations = []
    seen: set[str] = set()
    for r in results:
        c = r.chunk
        if c.chunk_id in seen:
            continue
        seen.add(c.chunk_id)
        page = c.metadata.get("page")
        para = c.metadata.get("paragraph")
        loc = f"page {page}" if page else f"paragraph {para}" if para else "unknown location"
        citations.append(f"[{len(citations)+1}] {c.metadata.get('filename')}, {loc}, chunk_id={c.chunk_id}")
    return citations

