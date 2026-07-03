from __future__ import annotations

from pathlib import Path

from src.models import DocumentSegment
from src.utils.text_utils import detect_language, normalize_text


def load_docx(path: Path, base_metadata: dict) -> list[DocumentSegment]:
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("DOCX support requires python-docx. Install requirements.txt.") from exc
    doc = Document(str(path))
    segments: list[DocumentSegment] = []
    heading = ""
    para_no = 0
    for para in doc.paragraphs:
        text = normalize_text(para.text)
        if not text:
            continue
        para_no += 1
        if para.style and para.style.name.lower().startswith("heading"):
            heading = text
        segments.append(
            DocumentSegment(
                text=text,
                metadata={
                    **base_metadata,
                    "paragraph": para_no,
                    "page": None,
                    "heading": heading,
                    "language": detect_language(text),
                },
            )
        )
    return segments

