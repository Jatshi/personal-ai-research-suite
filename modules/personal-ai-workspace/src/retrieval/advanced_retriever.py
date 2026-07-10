from __future__ import annotations

from typing import Any, Callable

from src.generation.llm_client import BaseLLMClient
from src.retrieval.adaptive_router import decide_route
from src.retrieval.context_compressor import compress_context
from src.retrieval.multi_hop_retriever import retrieve_multi_hop
from src.retrieval.query_rewriter import QueryRewriter


SearchFn = Callable[[str, int, str | None], list[dict[str, Any]]]


class AdvancedRetriever:
    def __init__(self, config: dict[str, Any], llm: BaseLLMClient, search_fn: SearchFn) -> None:
        self.config = config
        self.llm = llm
        self.search_fn = search_fn

    def search(self, query: str, top_k: int, collection: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        cfg = self.config["retrieval"]
        rewriter = QueryRewriter(self.llm, str(cfg.get("query_rewrite", "none")), int(cfg.get("max_subqueries", 3)))
        variants = rewriter.rewrite(query)
        merged: dict[str, dict[str, Any]] = {}
        for variant in variants:
            for result in self.search_fn(variant.text, top_k, collection):
                item = dict(result)
                item.setdefault("query_variant", variant.kind)
                merged.setdefault(item["chunk_id"], item)
        results = sorted(merged.values(), key=lambda item: item.get("score", 0.0), reverse=True)[:top_k]
        decision = decide_route(query, results, float(cfg["min_confidence"])) if cfg.get("crag_enabled", False) else None
        if decision and decision.route == "medium":
            results = self.search_fn(query, int(cfg.get("crag_expand_top_k", top_k * 2)), collection)[:top_k]
        if cfg.get("multi_hop_enabled", False) and results and (not decision or decision.route != "low"):
            results, hops = retrieve_multi_hop(query, results, lambda value, size: self.search_fn(value, size, collection), int(cfg.get("max_hops", 2)), top_k)
        else:
            hops = [{"hop": 1, "query": query, "result_count": len(results)}]
        compressed, compression = compress_context(
            query,
            results,
            str(cfg.get("context_compression", "none")),
            int(cfg.get("max_context_chars", cfg.get("max_context_tokens", 4096) * 4)),
            self.llm if cfg.get("context_compression") == "extractive" else None,
        )
        trace = {
            "original_query": query,
            "query_variants": [variant.__dict__ for variant in variants],
            "route": decision.__dict__ if decision else None,
            "hops": hops,
            "compression": compression,
        }
        return compressed, trace
