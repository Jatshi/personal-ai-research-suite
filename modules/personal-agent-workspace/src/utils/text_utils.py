from __future__ import annotations

import re
from collections import Counter


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "一个",
    "以及",
    "可以",
    "进行",
    "主要",
    "本文",
    "研究",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def top_keywords(text: str, n: int = 8) -> list[str]:
    counts = Counter(t for t in tokenize(text) if t not in STOPWORDS and len(t) > 1)
    return [k for k, _ in counts.most_common(n)]


def extract_year(text: str) -> str:
    match = re.search(r"\b(20\d{2}|19\d{2})\b", text or "")
    return match.group(1) if match else "unknown_year"
