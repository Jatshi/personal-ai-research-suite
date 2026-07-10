from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from src.chunking.chunker import chunk_text
from src.config.config_loader import resolve_project_path
from src.generation.factory import build_embedding_client
from src.indexing.chroma_store import upsert_chunks_to_chroma
from src.ingestion.document_loader import load_document
from src.storage.sqlite_store import SQLiteStore
from src.utils.hash_utils import sha256_text


def ingest_path(config: dict[str, Any], path: str, collection: str, source_type: str = "file", tags: list[str] | None = None) -> list[dict[str, Any]]:
    root = Path(path)
    if not root.is_absolute():
        root = resolve_project_path(config, root)
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".docx", ".pptx", ".md", ".txt", ".html", ".htm"}]
    store = SQLiteStore(config)
    embedder = build_embedding_client(config)
    docs = []
    for file in files:
        loaded = load_document(file)
        doc_id = sha256_text(f"{collection}:{file.resolve()}")[:16]
        meta = loaded["metadata"]
        doc = {
            "doc_id": doc_id,
            "file_name": file.name,
            "file_path": str(file.resolve()),
            "file_type": file.suffix.lower().lstrip("."),
            "collection": collection,
            "title": meta.get("title", file.stem),
            "author": meta.get("author", ""),
            "source_type": source_type,
            "language": meta.get("language", "unknown"),
            "tags": tags or [],
            "metadata": meta,
            "imported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        chunks = chunk_text(loaded["text"], doc, config["chunking"]["chunk_size"], config["chunking"]["chunk_overlap"])
        embeddings = embedder.embed_texts([c["text"] for c in chunks])
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb
        store.upsert_document(doc)
        store.add_chunks(chunks)
        upsert_chunks_to_chroma(config, collection, chunks)
        if config.get("graphrag", {}).get("auto_index", False):
            from src.graphrag.graph_index import NetworkXGraphIndex

            NetworkXGraphIndex(store).build(store.get_chunks(collection), collection)
        docs.append({**doc, "chunk_count": len(chunks)})
    return docs
