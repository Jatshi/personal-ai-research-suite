from __future__ import annotations

from typing import Any

from src.observability.trace_logger import JsonlLogger
from src.storage.sqlite_store import SQLiteStore


def dashboard_summary(config: dict[str, Any]) -> dict[str, Any]:
    store = SQLiteStore(config)
    return {
        "document_count": store.count_documents(),
        "recent_rag_queries": JsonlLogger(config, "rag_queries.jsonl").tail(5),
        "recent_tool_calls": JsonlLogger(config, "tool_calls.jsonl").tail(5),
        "recent_errors": JsonlLogger(config, "errors.jsonl").tail(5),
    }

