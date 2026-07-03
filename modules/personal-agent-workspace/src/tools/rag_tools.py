from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


def search_knowledge_base(query: str, rag_root: str = "../personal-academic-rag-workspace") -> dict:
    root = Path(rag_root).resolve()
    if not root.exists():
        return {"mode": "mock", "query": query, "results": ["Local RAG project not found; skipped external search."]}
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, "-m", "src.cli", "search", "--query", query, "--mode", "hybrid", "--top-k", "3"],
        cwd=root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    if proc.returncode != 0:
        return {"mode": "local_rag_cli", "query": query, "success": False, "error": proc.stderr[-1000:]}
    return {"mode": "local_rag_cli", "query": query, "success": True, "results": proc.stdout[-4000:]}
