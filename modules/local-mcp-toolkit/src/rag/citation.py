from __future__ import annotations


def citation_from_chunk(chunk: dict) -> dict:
    return {
        "doc_id": chunk.get("doc_id"),
        "title": chunk.get("title"),
        "file_path": chunk.get("file_path"),
        "chunk_id": chunk.get("chunk_id"),
        "snippet": chunk.get("snippet", chunk.get("text", ""))[:300],
    }

