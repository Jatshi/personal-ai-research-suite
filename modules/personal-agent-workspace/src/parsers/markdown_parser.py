from __future__ import annotations

from pathlib import Path


def parse_markdown(path: Path, max_chars: int = 12000) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]

