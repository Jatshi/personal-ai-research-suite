from __future__ import annotations

import re
from pathlib import Path

from src.models import DocumentSegment
from src.utils.text_utils import detect_language, normalize_text


def load_markdown(path: Path, base_metadata: dict) -> list[DocumentSegment]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    segments: list[DocumentSegment] = []
    heading = ""
    para_no = 0
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", block)
        if m:
            heading = m.group(2).strip()
        para_no += 1
        clean = normalize_text(block)
        segments.append(
            DocumentSegment(
                text=clean,
                metadata={
                    **base_metadata,
                    "paragraph": para_no,
                    "page": None,
                    "heading": heading,
                    "language": detect_language(clean),
                },
            )
        )
    return segments

