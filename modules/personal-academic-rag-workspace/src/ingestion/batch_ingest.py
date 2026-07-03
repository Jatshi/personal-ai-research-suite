from __future__ import annotations

from pathlib import Path

from src.indexing.index_manager import IndexManager


def batch_ingest(manager: IndexManager, path: str | Path, collection: str, tags: list[str] | None = None, doc_type: str = "general") -> list[str]:
    return manager.ingest_path(path, collection=collection, tags=tags, doc_type=doc_type)

