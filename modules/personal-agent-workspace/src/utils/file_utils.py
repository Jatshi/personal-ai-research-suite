from __future__ import annotations

from pathlib import Path


DOC_EXTENSIONS = {".pdf", ".docx", ".pptx", ".md", ".txt"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
CODE_EXTENSIONS = {".py", ".ipynb", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c"}


def is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

