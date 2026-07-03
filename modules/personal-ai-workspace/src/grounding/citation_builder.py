from __future__ import annotations

from typing import Any


def build_citations(chunks: list[dict[str, Any]]) -> list[str]:
    citations = []
    for i, c in enumerate(chunks, start=1):
        loc = c.get("section_title") or f"paragraph {c.get('paragraph_number')}"
        if c.get("page_number"):
            loc = f"page {c['page_number']}"
        citations.append(f"[{i}] {c.get('file_name')}, {loc}, chunk_id={c.get('chunk_id')}")
    return citations

