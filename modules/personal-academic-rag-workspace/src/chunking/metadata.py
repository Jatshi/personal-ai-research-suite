from __future__ import annotations

import hashlib


def make_doc_id(path: str, collection: str) -> str:
    return hashlib.sha1(f"{collection}:{path}".encode("utf-8")).hexdigest()[:16]


def make_chunk_id(doc_id: str, index: int, text: str) -> str:
    digest = hashlib.sha1(f"{doc_id}:{index}:{text[:200]}".encode("utf-8")).hexdigest()[:12]
    return f"{doc_id}-{index:04d}-{digest}"

