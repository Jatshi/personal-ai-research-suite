from __future__ import annotations

from pathlib import Path


def parse_pdf(path: Path, max_pages: int = 5) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        try:
            import PyPDF2

            PdfReader = PyPDF2.PdfReader
        except Exception:
            return "[PDF parser unavailable: install pypdf]"
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages[:max_pages]:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)

