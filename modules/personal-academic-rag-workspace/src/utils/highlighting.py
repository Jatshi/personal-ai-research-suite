from __future__ import annotations

import html
import re

from src.utils.text_utils import tokenize


def highlight_keywords(text: str, query: str) -> str:
    safe = html.escape(text)
    terms = sorted(set(tokenize(query)), key=len, reverse=True)
    for term in terms:
        if not term:
            continue
        safe = re.sub(re.escape(html.escape(term)), f"<mark>{html.escape(term)}</mark>", safe, flags=re.I)
    return safe

