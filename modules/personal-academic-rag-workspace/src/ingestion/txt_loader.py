from __future__ import annotations

from pathlib import Path

from src.models import DocumentSegment
from src.utils.text_utils import detect_language, normalize_text


def load_txt(path: Path, base_metadata: dict) -> list[DocumentSegment]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    paragraphs = [normalize_text(p) for p in text.splitlines() if normalize_text(p)]
    if not paragraphs and normalize_text(text):
        paragraphs = [normalize_text(text)]
    return [
        DocumentSegment(
            text=p,
            metadata={**base_metadata, "paragraph": i + 1, "page": None, "language": detect_language(p)},
        )
        for i, p in enumerate(paragraphs)
    ]

