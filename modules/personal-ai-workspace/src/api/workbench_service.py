from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from collections import Counter
from typing import Any

from src.observability.trace_logger import JsonlLogger
from src.observability.trace_logger import log_event
from src.config.config_loader import save_config
from src.config.config_loader import resolve_project_path
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
    query_events = JsonlLogger(config, LOG_FILES["rag"]).tail(500)
    confidence_values = [float(event["confidence"]) for event in query_events if isinstance(event.get("confidence"), (int, float))]
    recent_queries = [
        {
            "query": str(event.get("query", "")),
            "timestamp": event.get("timestamp"),
            "confidence": event.get("confidence"),
            "collection": event.get("collection"),
            "retrieved_chunks": len(event.get("retrieved_chunks", [])),
        }
        for event in query_events
        if event.get("query")
    ][-8:][::-1]
    return {
        "success": True,
        "documents": len(documents),
        "chunks": len(chunks),
        "collections": [{"name": name, "count": count} for name, count in sorted(collections.items())],
        "file_types": [{"name": name, "count": count} for name, count in sorted(file_types.items())],
        "graph": {"nodes": len(nodes), "edges": len(edges)},
        "queries": {
            "total": len(query_events),
            "average_confidence": round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else None,
            "trend": _query_trend(query_events),
            "recent": recent_queries,
        },
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


def observability_health(config: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive runtime status for the product health surface."""
    from src.cli import doctor_llm

    summary = dashboard_summary(config)
    data_dir = resolve_project_path(config, config.get("app", {}).get("data_dir", "./data"))
    usage = shutil.disk_usage(data_dir)
    provider = doctor_llm(config, call_api=False)
    return {
        "success": True,
        "llm": {
            "backend": provider.get("llm_backend"),
            "model": config.get("llm", {}).get("model_name"),
            "client": provider.get("llm_client"),
            "ready": provider.get("success", False),
        },
        "embedding": {
            "backend": provider.get("embedding_backend"),
            "model": config.get("embedding", {}).get("model_name"),
            "dimension": config.get("embedding", {}).get("dimension"),
            "client": provider.get("embedding_client"),
            "ready": provider.get("success", False),
        },
        "index": {
            "backend": config.get("vector_store", {}).get("backend", "sqlite"),
            "documents": summary["documents"],
            "chunks": summary["chunks"],
            "graph_nodes": summary["graph"]["nodes"],
            "graph_edges": summary["graph"]["edges"],
        },
        "storage": {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "used_percent": round(usage.used / usage.total * 100, 1) if usage.total else 0.0,
        },
    }


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


SETTINGS_FIELDS: dict[str, set[str]] = {
    "llm": {"backend", "model_name", "temperature", "max_tokens", "timeout_seconds"},
    "embedding": {"backend", "model_name", "dimension", "timeout_seconds"},
    "retrieval": {
        "default_mode", "backend", "top_k", "bm25_weight", "vector_weight",
        "query_rewrite", "context_compression", "crag_enabled", "multi_hop_enabled", "min_confidence",
    },
    "graphrag": {"enabled", "backend", "auto_index"},
    "agent": {"execution_mode", "max_iterations", "enable_long_term_memory"},
    "safety": {"require_dry_run_for_write", "require_confirmation_for_write", "block_hidden_files", "block_sensitive_files"},
}


def plan_settings_update(config: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(changes, dict) or not changes:
        raise ValueError("changes must contain at least one permitted settings section.")
    updated = deepcopy(config)
    diff: dict[str, dict[str, Any]] = {}
    for section, values in changes.items():
        if section not in SETTINGS_FIELDS or not isinstance(values, dict):
            raise ValueError(f"Unsupported settings section: {section}")
        for key, value in values.items():
            if key not in SETTINGS_FIELDS[section]:
                raise ValueError(f"Unsupported setting: {section}.{key}")
            _validate_setting(section, key, value)
            previous = updated.setdefault(section, {}).get(key)
            if previous != value:
                updated[section][key] = value
                diff[f"{section}.{key}"] = {"before": previous, "after": value}
    if "retrieval.bm25_weight" in diff or "retrieval.vector_weight" in diff:
        total = float(updated["retrieval"].get("bm25_weight", 0)) + float(updated["retrieval"].get("vector_weight", 0))
        if abs(total - 1.0) > 0.001:
            raise ValueError("retrieval.bm25_weight and retrieval.vector_weight must sum to 1.0.")
    return {"updated": updated, "diff": diff}


def update_settings(config: dict[str, Any], changes: dict[str, Any], confirm: bool) -> dict[str, Any]:
    plan = plan_settings_update(config, changes)
    response = {"success": True, "executed": False, "requires_confirmation": True, "plan": {"operation": "update_settings", "changes": plan["diff"], "dry_run": True}}
    if not confirm:
        log_event(config, "settings_changes.jsonl", response)
        return response
    updated = plan["updated"]
    save_config(updated, config.get("_config_path"))
    config.clear()
    config.update(updated)
    response.update({"executed": True, "requires_confirmation": False, "plan": {"operation": "update_settings", "changes": plan["diff"], "dry_run": False}})
    log_event(config, "settings_changes.jsonl", response)
    return response


def _pick(source: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: source[key] for key in keys if key in source}


def _validate_setting(section: str, key: str, value: Any) -> None:
    enum_values = {
        "retrieval.default_mode": {"hybrid", "keyword", "semantic", "graphrag", "hybrid+graphrag"},
        "retrieval.backend": {"hybrid", "graphrag", "hybrid+graphrag"},
        "retrieval.query_rewrite": {"none", "hyde", "decomposition"},
        "retrieval.context_compression": {"none", "token_budget", "extractive"},
        "graphrag.backend": {"networkx", "lightrag"},
        "agent.execution_mode": {"planner", "react"},
    }
    allowed = enum_values.get(f"{section}.{key}")
    if allowed is not None:
        if value not in allowed:
            raise ValueError(f"{section}.{key} must be one of: {', '.join(sorted(allowed))}.")
        return
    if key in {"top_k", "max_tokens", "timeout_seconds", "dimension", "max_iterations"}:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{section}.{key} must be a positive integer.")
    elif key in {"temperature", "bm25_weight", "vector_weight", "min_confidence"}:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 2:
            raise ValueError(f"{section}.{key} must be a number between 0 and 2.")
    elif key.endswith("enabled") or key.startswith("require_") or key.startswith("block_"):
        if not isinstance(value, bool):
            raise ValueError(f"{section}.{key} must be a boolean.")
    elif not isinstance(value, str):
        raise ValueError(f"{section}.{key} must be a string.")


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


def _query_trend(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a stable seven-day, local-time-independent query series from JSONL."""
    today = datetime.now(timezone.utc).date()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    counts = Counter()
    for event in events:
        timestamp = event.get("timestamp")
        if not isinstance(timestamp, str):
            continue
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        counts[parsed.isoformat()] += 1
    return [{"date": day.isoformat(), "count": counts[day.isoformat()]} for day in days]
