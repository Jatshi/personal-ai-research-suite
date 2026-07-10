from __future__ import annotations

import hashlib
from collections import Counter
from itertools import combinations
from typing import Any

from src.storage.sqlite_store import SQLiteStore
from src.utils.text_utils import tokenize


class NetworkXGraphIndex:
    """Deterministic entity co-occurrence graph persisted in the workspace DB."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def build(self, chunks: list[dict[str, Any]], collection: str | None = None) -> dict[str, int]:
        node_map: dict[str, dict[str, Any]] = {}
        links: list[dict[str, Any]] = []
        edge_counts: Counter[tuple[str, str]] = Counter()
        for chunk in chunks:
            terms = _entities(chunk.get("text", ""))
            ids = []
            for term in terms:
                node_id = _node_id(term)
                ids.append(node_id)
                node_map[node_id] = {"node_id": node_id, "label": term, "node_type": "concept", "collection": collection, "metadata": {}}
                links.append({"node_id": node_id, "chunk_id": chunk["chunk_id"], "collection": collection, "weight": 1.0})
            edge_counts.update(tuple(sorted(pair)) for pair in combinations(sorted(set(ids)), 2))
        edges = [
            {"source_id": source, "target_id": target, "relation": "co_occurs", "weight": float(weight), "collection": collection}
            for (source, target), weight in edge_counts.items()
        ]
        self.store.replace_graph(collection, list(node_map.values()), edges, links)
        return {"node_count": len(node_map), "edge_count": len(edges), "link_count": len(links)}


def _entities(text: str) -> list[str]:
    return [term for term in dict.fromkeys(tokenize(text)) if len(term) >= 4][:24]


def _node_id(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()[:16]
