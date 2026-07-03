from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

from src.models import Chunk, SearchResult
from src.utils.text_utils import tokenize


class BM25Store:
    def __init__(self, chunks: list[Chunk] | None = None, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.chunks = chunks or []
        self.doc_tokens = [tokenize(c.text) for c in self.chunks]
        self.avgdl = sum(len(t) for t in self.doc_tokens) / len(self.doc_tokens) if self.doc_tokens else 0.0
        self.df: dict[str, int] = defaultdict(int)
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.df[token] += 1

    def search(self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[SearchResult]:
        filters = filters or {}
        q = tokenize(query)
        if not q:
            return []
        scores = []
        n = len(self.chunks)
        for chunk, tokens in zip(self.chunks, self.doc_tokens):
            if filters.get("collection") and chunk.metadata.get("collection") != filters["collection"]:
                continue
            if filters.get("doc_type") and chunk.metadata.get("doc_type") != filters["doc_type"]:
                continue
            tf = Counter(tokens)
            score = 0.0
            dl = len(tokens) or 1
            for term in q:
                if term not in tf:
                    continue
                idf = math.log(1 + (n - self.df.get(term, 0) + 0.5) / (self.df.get(term, 0) + 0.5))
                score += idf * (tf[term] * (self.k1 + 1)) / (tf[term] + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1)))
            if score > 0:
                scores.append(SearchResult(chunk=chunk, score=score, bm25_score=score))
        if not scores:
            return []
        max_score = max(s.score for s in scores) or 1.0
        for s in scores:
            s.score = s.bm25_score = s.score / max_score
        return sorted(scores, key=lambda x: x.score, reverse=True)[:top_k]

