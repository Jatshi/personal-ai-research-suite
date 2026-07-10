from __future__ import annotations

import re
import uuid
from typing import Any

from src.storage.sqlite_store import SQLiteStore


class MemoryStore:
    """SQLite-backed long-term memory with explicit sensitive-data filtering."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.store = SQLiteStore(config)

    def add(self, scope: str, content: str, metadata: dict[str, Any] | None = None, importance: float = 0.5) -> dict[str, Any] | None:
        if not content.strip() or _looks_sensitive(content):
            return None
        memory = {
            "memory_id": uuid.uuid4().hex,
            "scope": scope,
            "content": content.strip()[:2000],
            "metadata": metadata or {},
            "importance": max(0.0, min(float(importance), 1.0)),
        }
        self.store.add_memory(memory)
        return memory

    def search(self, scope: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", query)}
        memories = self.store.list_memories(scope, limit=100)
        ranked = []
        for memory in memories:
            text = memory["content"].lower()
            score = sum(term in text for term in terms) + float(memory.get("importance", 0.0))
            if score > 0:
                ranked.append((score, memory))
        return [memory for _, memory in sorted(ranked, key=lambda item: item[0], reverse=True)[:limit]]

    def list(self, scope: str, limit: int = 50) -> list[dict[str, Any]]:
        return self.store.list_memories(scope, limit)


def _looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("api_key", "openai_api_key", "sk-", ".env", "password="))
