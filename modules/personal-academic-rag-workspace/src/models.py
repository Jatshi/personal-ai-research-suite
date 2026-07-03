from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentSegment:
    text: str
    metadata: dict[str, Any]


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    metadata: dict[str, Any]


@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float = 0.0
    debug: dict[str, Any] = field(default_factory=dict)


@dataclass
class Answer:
    text: str
    citations: list[str]
    confidence: float
    evidence: list[SearchResult]

