from __future__ import annotations

import json
from collections import Counter
from typing import Any

from src.observability.trace_logger import JsonlLogger
from src.storage.sqlite_store import SQLiteStore


LOG_FILES = {
    "rag": "rag_queries.jsonl",
    "tool": "tool_calls.jsonl",
    "agent": "agent_runs.jsonl",
    "multi_agent": "multi_agent_runs.jsonl",
    "evaluation": "evaluation.jsonl",
}


def dashboard_summary(config: dict[str, Any]) -> dict[str, Any]:
    """Return read-only aggregates for product surfaces without exposing document text."""
    store = SQLiteStore(config)
    documents = store.list_documents()
    chunks = store.get_chunks()
    collections = Counter(str(document.get("collection") or "unassigned") for document in documents)
    file_types = Counter(str(document.get("file_type") or "unknown") for document in documents)
    nodes, edges, _ = store.graph_snapshot()
    return {
        "success": True,
        "documents": len(documents),
        "chunks": len(chunks),
        "collections": [{"name": name, "count": count} for name, count in sorted(collections.items())],
        "file_types": [{"name": name, "count": count} for name, count in sorted(file_types.items())],
        "graph": {"nodes": len(nodes), "edges": len(edges)},
        "recent_documents": [_public_document(document) for document in documents[:8]],
    }


def document_detail(config: dict[str, Any], doc_id: str, chunk_limit: int = 20) -> dict[str, Any] | None:
    store = SQLiteStore(config)
    document = next((item for item in store.list_documents() if item.get("doc_id") == doc_id), None)
    if not document:
        return None
    chunks = [item for item in store.get_chunks(document.get("collection")) if item.get("doc_id") == doc_id]
    return {
        "success": True,
        "document": _public_document(document),
        "chunks": [_public_chunk(chunk) for chunk in chunks[:chunk_limit]],
        "chunk_count": len(chunks),
    }


def observability_events(config: dict[str, Any], category: str | None = None, limit: int = 50) -> dict[str, Any]:
    categories = [category] if category else list(LOG_FILES)
    invalid = [item for item in categories if item not in LOG_FILES]
    if invalid:
        raise ValueError(f"Unknown log category: {', '.join(invalid)}")
    events: list[dict[str, Any]] = []
    for item in categories:
        for event in JsonlLogger(config, LOG_FILES[item]).tail(limit):
            events.append({"category": item, **event})
    events.sort(key=lambda item: str(item.get("timestamp", "")), reverse=True)
    return {"success": True, "events": events[:limit], "categories": categories}


def public_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Expose operational settings without paths, API key names, or other credentials."""
    return {
        "success": True,
        "llm": _pick(config.get("llm", {}), "backend", "model_name", "temperature", "max_tokens", "timeout_seconds"),
        "embedding": _pick(config.get("embedding", {}), "backend", "model_name", "dimension", "timeout_seconds"),
        "retrieval": _pick(config.get("retrieval", {}), "default_mode", "backend", "top_k", "bm25_weight", "vector_weight", "query_rewrite", "context_compression", "crag_enabled", "multi_hop_enabled"),
        "graphrag": _pick(config.get("graphrag", {}), "enabled", "backend", "auto_index"),
        "agent": _pick(config.get("agent", {}), "execution_mode", "max_iterations", "enable_long_term_memory"),
        "safety": _pick(config.get("safety", {}), "restrict_to_workspace", "require_dry_run_for_write", "require_confirmation_for_write", "allow_delete"),
    }


def _pick(source: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: source[key] for key in keys if key in source}


def _public_document(document: dict[str, Any]) -> dict[str, Any]:
    result = dict(document)
    for key in ("metadata", "tags"):
        value = result.get(key)
        if isinstance(value, str):
            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:
                pass
    return result


def _public_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": chunk.get("chunk_id"),
        "section_title": chunk.get("section_title"),
        "page_number": chunk.get("page_number"),
        "paragraph_number": chunk.get("paragraph_number"),
        "text": str(chunk.get("text", ""))[:4000],
    }
