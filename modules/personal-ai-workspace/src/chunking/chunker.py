from __future__ import annotations

import re
from typing import Any

from src.utils.hash_utils import sha256_text


def chunk_text(text: str, doc: dict[str, Any], chunk_size: int = 800, chunk_overlap: int = 120) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    chunks: list[dict[str, Any]] = []
    buf = ""
    start_para = 1
    section = ""
    for i, para in enumerate(paragraphs, start=1):
        if para.startswith("#"):
            section = para.lstrip("#").strip()
        if len(buf) + len(para) + 2 > chunk_size and buf:
            chunks.append(_make_chunk(buf, doc, len(chunks), start_para, section))
            buf = buf[-chunk_overlap:] if chunk_overlap > 0 else ""
            start_para = i
        buf = (buf + "\n\n" + para).strip()
    if buf:
        chunks.append(_make_chunk(buf, doc, len(chunks), start_para, section))
    return chunks


def _make_chunk(text: str, doc: dict[str, Any], idx: int, para: int, section: str) -> dict[str, Any]:
    page_match = re.search(r"\[Page\s+(\d+)\]", text)
    chunk_seed = f"{doc['doc_id']}:{idx}:{text[:80]}"
    return {
        "chunk_id": sha256_text(chunk_seed)[:16],
        "doc_id": doc["doc_id"],
        "collection": doc["collection"],
        "file_name": doc["file_name"],
        "section_title": section,
        "page_number": int(page_match.group(1)) if page_match else None,
        "paragraph_number": para,
        "text": text,
        "metadata": {"source_type": doc.get("source_type", "file")},
    }

