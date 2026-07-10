from __future__ import annotations

import copy
from typing import Any

from src.generation.answer_generator import generate_grounded_answer
from src.generation.factory import build_embedding_client, build_llm_client
from src.indexing.chroma_store import chroma_enabled, search_chroma
from src.indexing.index_manager import ingest_path
from src.observability.trace_logger import log_event
from src.retrieval.hybrid_retriever import search_chunks
from src.retrieval.advanced_retriever import AdvancedRetriever
from src.graphrag.graph_retriever import GraphRAGRetriever
from src.storage.sqlite_store import SQLiteStore


def ingest_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    docs = ingest_path(config, args["path"], args.get("collection", "personal"), tags=args.get("tags") or [])
    return {"success": True, "documents": docs}


def list_docs_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    docs = SQLiteStore(config).list_documents(args.get("collection"))
    return {"success": True, "documents": docs}


def search_kb_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    effective_config = copy.deepcopy(config)
    for key in ("query_rewrite", "context_compression", "crag_enabled", "multi_hop_enabled"):
        if key in args and args[key] is not None:
            effective_config["retrieval"][key] = args[key]
    top_k = int(args.get("top_k") or effective_config["retrieval"]["top_k"])
    mode = args.get("mode") or effective_config["retrieval"]["default_mode"]

    def base_search(query: str, limit: int, collection: str | None) -> list[dict[str, Any]]:
        return _base_search(effective_config, query, limit, collection, mode)

    retriever = AdvancedRetriever(effective_config, build_llm_client(effective_config), base_search)
    results, trace = retriever.search(args["query"], top_k, args.get("collection"))
    public_results = [_public_chunk(r) for r in results]
    log_event(
        effective_config,
        "rag_queries.jsonl",
        {
            "query": args["query"],
            "collection": args.get("collection"),
            "retrieval_mode": mode,
            "top_k": top_k,
            "retrieved_chunks": [r["chunk_id"] for r in public_results],
            "scores": [r.get("score") for r in public_results],
            "retrieval_trace": trace,
            "success": True,
        },
    )
    return {"success": True, "query": args["query"], "results": public_results, "retrieval_trace": trace}


def _base_search(config: dict[str, Any], query: str, top_k: int, collection: str | None, mode: str) -> list[dict[str, Any]]:
    store = SQLiteStore(config)
    if mode == "graphrag" or (mode == "hybrid" and config.get("retrieval", {}).get("backend") == "graphrag"):
        return GraphRAGRetriever(store).search(query, collection, top_k)
    chunks = store.get_chunks(collection)
    embedder = build_embedding_client(config) if mode != "keyword" else None
    semantic_results = None
    if embedder is not None and chroma_enabled(config):
        semantic_results = search_chroma(config, collection, embedder.embed_query(query), top_k * 2)
    results = search_chunks(
        chunks,
        query,
        mode=mode,
        top_k=top_k,
        bm25_weight=float(config["retrieval"]["bm25_weight"]),
        vector_weight=float(config["retrieval"]["vector_weight"]),
        embedding_dim=int(config["embedding"]["dimension"]),
        embedder=embedder,
        semantic_results=semantic_results,
    )
    if mode == "hybrid+graphrag" or (mode == "hybrid" and config.get("retrieval", {}).get("backend") == "hybrid+graphrag"):
        graph_results = GraphRAGRetriever(store).search(query, collection, top_k * 2)
        merged = {item["chunk_id"]: item for item in results}
        for item in graph_results:
            existing = merged.get(item["chunk_id"])
            if existing:
                existing["graph_score"] = item.get("graph_score", 0.0)
                existing["score"] = existing.get("score", 0.0) + 0.15 * item.get("graph_score", 0.0)
            else:
                merged[item["chunk_id"]] = item
        return sorted(merged.values(), key=lambda item: item.get("score", 0.0), reverse=True)[:top_k]
    return results


def ask_kb_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    search = search_kb_tool(config, args)
    route = (search.get("retrieval_trace") or {}).get("route") or {}
    if route.get("route") == "low":
        from src.grounding.evidence_checker import NO_EVIDENCE

        return {"success": True, "answer": NO_EVIDENCE, "confidence": route.get("confidence", 0.0), "citations": [], "evidence": search["results"], "retrieval_trace": search["retrieval_trace"]}
    answer = generate_grounded_answer(args["query"], search["results"], float(config["retrieval"]["min_confidence"]), config)
    return {"success": True, **answer, "retrieval_trace": search["retrieval_trace"]}


def summarize_doc_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    chunks = [c for c in SQLiteStore(config).get_chunks(args.get("collection")) if c["doc_id"] == args.get("doc_id") or c["file_name"] == args.get("file_name")]
    text = "\n".join(c["text"] for c in chunks[:3])
    prompt = "请基于给定文档片段生成简明摘要，不要补充片段外的信息。"
    return {"success": True, "summary": build_llm_client(config).generate(prompt, [{"text": text, "file_name": args.get("file_name", args.get("doc_id", ""))}])}


def _public_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    item = dict(chunk)
    item.pop("embedding", None)
    item["snippet"] = item.get("text", "")[:280]
    return item
