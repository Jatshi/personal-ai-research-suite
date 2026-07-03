from __future__ import annotations

import re
from pathlib import Path


def find_todo_markers(root: Path, ignored_dirs: set[str], markers: list[str]) -> dict:
    todos = []
    pat = re.compile(r"\b(" + "|".join(re.escape(m) for m in markers) + r")\b[:\s]*(.*)", re.I)
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored_dirs or part.startswith(".") for part in path.relative_to(root).parts):
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            m = pat.search(line)
            if m:
                todos.append({"path": str(path.relative_to(root)), "line_number": i, "marker": m.group(1).upper(), "text": m.group(2).strip()})
    return {"todos": todos}

