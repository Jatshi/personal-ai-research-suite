from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {"the", "and", "of", "to", "a", "in", "is", "for", "with", "on", "了", "的", "和", "是", "在"}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    words = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text)
    return [w for w in words if w and w not in STOPWORDS]


def keyword_summary(text: str, max_terms: int = 8) -> list[str]:
    counts = Counter(tokenize(text))
    return [w for w, _ in counts.most_common(max_terms)]


def first_sentences(text: str, max_chars: int = 500) -> str:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."

