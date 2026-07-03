from __future__ import annotations

import re
from pathlib import Path


def parse_code(path: Path, max_lines: int = 160) -> str:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_lines]
    interesting = []
    for line in lines:
        s = line.strip()
        if s.startswith(("#", "//", "/*", "*")) or re.match(r"(def|class|function|const|let|var|public|private)\s+", s):
            interesting.append(line)
    return "\n".join(interesting or lines[:40])

