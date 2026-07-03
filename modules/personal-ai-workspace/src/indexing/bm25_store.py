from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

from src.utils.text_utils import tokenize


def bm25_search(chunks: list[dict[str, Any]], query: str, top_k: int) -> list[dict[str, Any]]:
    q_terms = tokenize(query)
    if not q_terms:
        return []
    tokenized = [tokenize(c.get("text", "")) for c in chunks]
    avgdl = sum(len(t) for t in tokenized) / max(len(tokenized), 1)
    df: dict[str, int] = defaultdict(int)
    for toks in tokenized:
        for term in set(toks):
            df[term] += 1
    n = len(chunks)
    scored = []
    for chunk, toks in zip(chunks, tokenized):
        counts = Counter(toks)
        dl = len(toks) or 1
        score = 0.0
        for term in q_terms:
            if counts[term] == 0:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (counts[term] * 2.2) / (counts[term] + 1.2 * (1 - 0.75 + 0.75 * dl / (avgdl or 1)))
        item = dict(chunk)
        item["bm25_score"] = score
        item["score"] = score
        scored.append(item)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

