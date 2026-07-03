from __future__ import annotations

from pathlib import Path

from src.models import DocumentSegment
from src.utils.text_utils import detect_language, normalize_text


def load_pdf(path: Path, base_metadata: dict) -> list[DocumentSegment]:
    try:
        from pypdf import PdfReader
    except Exception:
        try:
            import PyPDF2

            PdfReader = PyPDF2.PdfReader
        except Exception as exc:
            raise RuntimeError("PDF support requires pypdf or PyPDF2. Install requirements.txt.") from exc
    reader = PdfReader(str(path))
    segments: list[DocumentSegment] = []
    for i, page in enumerate(reader.pages):
        text = normalize_text(page.extract_text() or "")
        if not text:
            continue
        segments.append(
            DocumentSegment(
                text=text,
                metadata={**base_metadata, "page": i + 1, "paragraph": None, "language": detect_language(text)},
            )
        )
    return segments

