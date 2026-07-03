from __future__ import annotations

from pathlib import Path

from src.utils.file_utils import language_for_extension


def search_code_files(root: Path, query: str, ignored_dirs: set[str], extensions: list[str] | None = None, limit: int = 50) -> dict:
    exts = set(extensions or [])
    matches = []
    for path in root.rglob("*"):
        if len(matches) >= limit:
            break
        if not path.is_file() or any(part in ignored_dirs or part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if exts and path.suffix.lower() not in exts:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            if query.lower() in line.lower():
                matches.append({"path": str(path.relative_to(root)), "line_number": i, "snippet": line.strip()[:300], "language": language_for_extension(path.suffix)})
                break
    return {"query": query, "matches": matches}

