from __future__ import annotations

import math
import re
from collections import Counter


_LATIN_RE = re.compile(r"[A-Za-z0-9_]+")
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")

# A small deterministic bridge keeps the offline retriever useful when a Chinese
# query targets English personal material. A full translation model can replace it.
_ZH_QUERY_HINTS = {
    "\u65b9\u6cd5": ["method", "methods", "methodology", "approach"],
    "\u8bba\u6587": ["paper", "academic", "study"],
    "\u793a\u4f8b": ["demo", "demonstration", "example", "simulated"],
    "\u603b\u7ed3": ["summary", "conclusion", "abstract"],
    "\u7814\u7a76": ["research", "study"],
    "\u4e3b\u9898": ["theme", "themes", "topic"],
    "\u590d\u6742": ["complex"],
    "\u58f0\u5b66": ["acoustic"],
    "\u573a\u666f": ["scene", "scenes"],
    "\u6ce8\u610f\u529b": ["attention"],
    "\u8bc1\u636e": ["evidence"],
    "\u5f15\u7528": ["citation", "citations"],
    "\u7b80\u5386": ["resume", "career", "cv"],
    "\u9879\u76ee": ["project"],
    "\u535a\u58eb\u8bba\u6587": ["thesis", "dissertation"],
    "\u7cfb\u7edf": ["system", "rag"],
    "\u5e7b\u89c9": ["hallucination", "unsupported", "grounded"],
    "\u98ce\u9669": ["risk", "reliability"],
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def _cjk_ngrams(text: str) -> list[str]:
    terms: list[str] = []
    for run in _CJK_RUN_RE.findall(text):
        if len(run) == 1:
            terms.append(run)
            continue
        for n in (2, 3):
            if len(run) >= n:
                terms.extend(run[i : i + n] for i in range(len(run) - n + 1))
    return terms


def tokenize(text: str) -> list[str]:
    raw = text or ""
    tokens = [t.lower() for t in _LATIN_RE.findall(raw) if len(t) > 1 or t.isdigit()]
    tokens.extend(_cjk_ngrams(raw))
    for zh, hints in _ZH_QUERY_HINTS.items():
        if zh in raw:
            tokens.extend(hints)
    return tokens


def detect_language(text: str) -> str:
    zh = len(re.findall(r"[\u4e00-\u9fff]", text or ""))
    en = len(re.findall(r"[A-Za-z]", text or ""))
    if zh and zh >= en / 3:
        return "zh"
    if en:
        return "en"
    return "unknown"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(v * v for v in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def keyword_coverage(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0
    text_tokens = set(tokenize(text))
    overall = len(query_tokens & text_tokens) / len(query_tokens)

    # Preserve a named English technical term (for example, RAG or LoRA) as a
    # strong cross-language signal instead of diluting it with Chinese n-grams.
    latin_query = {term.lower() for term in _LATIN_RE.findall(query) if len(term) > 1}
    if not latin_query:
        return overall
    latin_coverage = len(latin_query & text_tokens) / len(latin_query)
    return max(overall, latin_coverage)


def top_terms(texts: list[str], n: int = 8) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(tokenize(text))
    return [term for term, _ in counts.most_common(n)]
