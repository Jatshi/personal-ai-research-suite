from __future__ import annotations

import re
from typing import Any

from src.utils.text_utils import first_sentences, keyword_summary


def extract_reading_metadata(text: str, source: str = "") -> dict[str, Any]:
    title = ""
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            title = stripped[:120]
            break
    date_match = re.search(r"(20\d{2}-\d{2}-\d{2}|20\d{2})", text)
    return {
        "title": title or source,
        "author": "",
        "publish_date": date_match.group(1) if date_match else "",
        "source_url": source,
        "tags": keyword_summary(text, 6),
        "summary": first_sentences(text, 260),
    }

