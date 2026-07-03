from __future__ import annotations

import math
import re
from collections import Counter


_LATIN_RE = re.compile(r"[A-Za-z0-9_]+")
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_ZH_QUERY_HINTS = {
    "方法": ["method", "methods", "methodology", "approach"],
    "论文": ["paper", "academic", "study"],
    "示例": ["demo", "demonstration", "example", "simulated"],
    "总结": ["summary", "conclusion", "abstract"],
    "研究": ["research", "study"],
    "主题": ["theme", "themes", "topic"],
    "复杂": ["complex"],
    "声学": ["acoustic"],
    "场景": ["scene", "scenes"],
    "注意力": ["attention"],
    "证据": ["evidence"],
    "引用": ["citation", "citations"],
    "求职": ["resume", "career"],
    "项目": ["project"],
    "博士": ["thesis", "dissertation"],
    "简历": ["resume", "cv"],
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
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def keyword_coverage(query: str, text: str) -> float:
    q = set(tokenize(query))
    if not q:
        return 0.0
    t = set(tokenize(text))
    return len(q & t) / len(q)


def top_terms(texts: list[str], n: int = 8) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(tokenize(text))
    return [term for term, _ in counts.most_common(n)]
