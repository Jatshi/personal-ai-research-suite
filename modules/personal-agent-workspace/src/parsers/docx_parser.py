from __future__ import annotations

from pathlib import Path


def parse_docx(path: Path, max_paragraphs: int = 80) -> str:
    try:
        from docx import Document
    except Exception:
        return "[DOCX parser unavailable: install python-docx]"
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs[:max_paragraphs] if p.text.strip())

