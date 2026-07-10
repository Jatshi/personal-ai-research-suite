from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.storage.sqlite_store import SQLiteStore
from src.utils.text_utils import tokenize


class GraphRAGRetriever:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def search(self, query: str, collection: str | None, top_k: int) -> list[dict[str, Any]]:
        nodes, edges, links = self.store.graph_snapshot(collection)
        query_terms = set(tokenize(query))
        matching = {node["node_id"] for node in nodes if node["label"] in query_terms}
        if not matching:
            return []
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            adjacency[edge["source_id"]].add(edge["target_id"])
            adjacency[edge["target_id"]].add(edge["source_id"])
        expanded = matching | {neighbor for node in matching for neighbor in adjacency[node]}
        scores: Counter[str] = Counter()
        for link in links:
            if link["node_id"] in expanded:
                scores[link["chunk_id"]] += 1.0 if link["node_id"] in matching else 0.35
        chunks = {chunk["chunk_id"]: chunk for chunk in self.store.get_chunks(collection)}
        results = []
        for chunk_id, score in scores.most_common(top_k):
            if chunk_id in chunks:
                item = dict(chunks[chunk_id])
                item["graph_score"] = score
                item["score"] = score
                results.append(item)
        return results
