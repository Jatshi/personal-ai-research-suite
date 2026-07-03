from __future__ import annotations

from src.chunking.metadata import make_chunk_id, make_doc_id
from src.models import Chunk, DocumentSegment
from src.utils.text_utils import normalize_text


class TextChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, segments: list[DocumentSegment]) -> list[Chunk]:
        chunks: list[Chunk] = []
        if not segments:
            return chunks
        doc_id = make_doc_id(segments[0].metadata["source_path"], segments[0].metadata["collection"])
        buffer = ""
        meta = dict(segments[0].metadata)
        idx = 0
        for seg in segments:
            text = normalize_text(seg.text)
            if not text:
                continue
            if len(buffer) + len(text) + 1 <= self.chunk_size:
                buffer = f"{buffer}\n{text}".strip()
                meta = self._merge_meta(meta, seg.metadata)
                continue
            if buffer:
                chunks.append(self._make_chunk(doc_id, idx, buffer, meta))
                idx += 1
                overlap = buffer[-self.chunk_overlap :] if self.chunk_overlap else ""
                buffer = f"{overlap}\n{text}".strip()
                meta = dict(seg.metadata)
            while len(buffer) > self.chunk_size * 1.5:
                part = buffer[: self.chunk_size]
                chunks.append(self._make_chunk(doc_id, idx, part, meta))
                idx += 1
                buffer = buffer[max(0, self.chunk_size - self.chunk_overlap) :]
        if buffer:
            chunks.append(self._make_chunk(doc_id, idx, buffer, meta))
        return chunks

    @staticmethod
    def _merge_meta(a: dict, b: dict) -> dict:
        merged = dict(a)
        for key in ("page", "paragraph"):
            if a.get(key) and b.get(key) and a.get(key) != b.get(key):
                merged[key] = f"{a.get(key)}-{b.get(key)}"
            elif b.get(key):
                merged[key] = b.get(key)
        for key, value in b.items():
            merged.setdefault(key, value)
        return merged

    @staticmethod
    def _make_chunk(doc_id: str, idx: int, text: str, metadata: dict) -> Chunk:
        chunk_id = make_chunk_id(doc_id, idx, text)
        return Chunk(chunk_id=chunk_id, doc_id=doc_id, text=text, metadata={**metadata, "doc_id": doc_id, "chunk_id": chunk_id})

