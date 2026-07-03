from __future__ import annotations

from pathlib import Path

from src.parsers.code_parser import parse_code
from src.parsers.docx_parser import parse_docx
from src.parsers.markdown_parser import parse_markdown
from src.parsers.pdf_parser import parse_pdf
from src.parsers.pptx_parser import parse_pptx
from src.utils.file_utils import CODE_EXTENSIONS, DOC_EXTENSIONS, IMAGE_EXTENSIONS


def read_document(path: str) -> dict:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        text = parse_pdf(p)
    elif ext == ".docx":
        text = parse_docx(p)
    elif ext == ".pptx":
        text = parse_pptx(p)
    elif ext in {".md", ".txt"}:
        text = parse_markdown(p)
    elif ext in CODE_EXTENSIONS:
        text = parse_code(p)
    elif ext in IMAGE_EXTENSIONS:
        text = f"[Image metadata only] filename={p.name}, size={p.stat().st_size}"
    else:
        text = p.read_text(encoding="utf-8", errors="ignore")[:8000]
    return {"path": str(p), "text": text[:12000], "extension": ext}


def summarize_file(path: str, llm) -> dict:
    doc = read_document(path)
    summary = llm.generate("summary", [{"text": doc["text"]}])
    return {**doc, "summary": summary}


def summarize_files(paths: list[str], llm) -> dict:
    return {"summaries": [summarize_file(path, llm) for path in paths]}

