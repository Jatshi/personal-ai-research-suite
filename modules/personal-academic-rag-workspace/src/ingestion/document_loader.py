from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.ingestion.docx_loader import load_docx
from src.ingestion.markdown_loader import load_markdown
from src.ingestion.pdf_loader import load_pdf
from src.ingestion.pptx_loader import load_pptx
from src.ingestion.txt_loader import load_txt
from src.models import DocumentSegment


LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".pptx": load_pptx,
    ".md": load_markdown,
    ".txt": load_txt,
}


def load_document(path: str | Path, collection: str = "personal", tags: list[str] | None = None, doc_type: str = "general") -> list[DocumentSegment]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in LOADERS:
        raise ValueError(f"Unsupported file type: {suffix}")
    stat = path.stat()
    base_metadata = {
        "filename": path.name,
        "source_path": str(path.resolve()),
        "file_type": suffix.lstrip("."),
        "collection": collection,
        "tags": tags or [],
        "date": datetime.fromtimestamp(stat.st_mtime).date().isoformat(),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "doc_type": doc_type,
    }
    return LOADERS[suffix](path, base_metadata)

