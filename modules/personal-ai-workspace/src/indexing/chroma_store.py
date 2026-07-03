from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.config.config_loader import resolve_project_path


def chroma_enabled(config: dict[str, Any]) -> bool:
    return str(config.get("vector_store", {}).get("backend", "sqlite")).lower() == "chroma"


def upsert_chunks_to_chroma(config: dict[str, Any], collection: str, chunks: list[dict[str, Any]]) -> None:
    if not chroma_enabled(config) or not chunks:
        return
    client = _client(config)
    col = client.get_or_create_collection(name=_collection_name(config, collection), metadata={"hnsw:space": "cosine"})
    col.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c.get("text", "") for c in chunks],
        metadatas=[_metadata_for_chroma(c) for c in chunks],
    )


def search_chroma(
    config: dict[str, Any],
    collection: str | None,
    query_embedding: list[float],
    top_k: int,
) -> list[dict[str, Any]]:
    if not chroma_enabled(config):
        return []
    client = _client(config)
    collections = [_collection_name(config, collection)] if collection else [c.name for c in client.list_collections()]
    results: list[dict[str, Any]] = []
    for name in collections:
        try:
            col = client.get_collection(name=name)
        except Exception:
            continue
        raw = col.query(query_embeddings=[query_embedding], n_results=max(1, top_k))
        ids = raw.get("ids", [[]])[0]
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0] if raw.get("distances") else [0.0] * len(ids)
        for cid, doc, meta, dist in zip(ids, docs, metas, distances):
            item = dict(meta or {})
            item["chunk_id"] = cid
            item["text"] = doc or item.get("text", "")
            item["vector_score"] = _distance_to_score(float(dist or 0.0))
            item["score"] = item["vector_score"]
            item["metadata"] = {"vector_store": "chroma", "distance": dist}
            results.append(item)
    return sorted(results, key=lambda x: x.get("vector_score", 0.0), reverse=True)[:top_k]


def delete_chroma_collection(config: dict[str, Any], collection: str) -> None:
    if not chroma_enabled(config):
        return
    client = _client(config)
    name = _collection_name(config, collection)
    try:
        client.delete_collection(name=name)
    except Exception:
        return


def delete_chroma_ids(config: dict[str, Any], collection: str | None, chunk_ids: list[str]) -> None:
    if not chroma_enabled(config) or not chunk_ids:
        return
    client = _client(config)
    collections = [_collection_name(config, collection)] if collection else [c.name for c in client.list_collections()]
    for name in collections:
        try:
            col = client.get_collection(name=name)
            col.delete(ids=chunk_ids)
        except Exception:
            continue


def _client(config: dict[str, Any]):
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "vector_store.backend=chroma requires chromadb. Install with `pip install -r requirements-production.txt`."
        ) from exc
    persist_dir = resolve_project_path(config, config.get("vector_store", {}).get("persist_dir", "./data/indexes/chroma"))
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def _collection_name(config: dict[str, Any], collection: str | None) -> str:
    prefix = config.get("vector_store", {}).get("collection_prefix", "personal_ai_workspace")
    raw = f"{prefix}_{collection or 'default'}"
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")
    return name[:63] or "personal_ai_workspace_default"


def _metadata_for_chroma(chunk: dict[str, Any]) -> dict[str, str | int | float | bool]:
    allowed = {
        "doc_id",
        "collection",
        "file_name",
        "section_title",
        "page_number",
        "paragraph_number",
    }
    out: dict[str, str | int | float | bool] = {}
    for key in allowed:
        value = chunk.get(key)
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            out[key] = value
        else:
            out[key] = str(value)
    return out


def _distance_to_score(distance: float) -> float:
    return max(0.0, min(1.0, 1.0 / (1.0 + distance)))
