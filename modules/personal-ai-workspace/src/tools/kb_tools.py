from __future__ import annotations

from typing import Any

from src.generation.answer_generator import generate_grounded_answer
from src.generation.factory import build_embedding_client, build_llm_client
from src.indexing.chroma_store import chroma_enabled, search_chroma
from src.indexing.index_manager import ingest_path
from src.observability.trace_logger import log_event
from src.retrieval.hybrid_retriever import search_chunks
from src.storage.sqlite_store import SQLiteStore


def ingest_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    docs = ingest_path(config, args["path"], args.get("collection", "personal"), tags=args.get("tags") or [])
    return {"success": True, "documents": docs}


def list_docs_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    docs = SQLiteStore(config).list_documents(args.get("collection"))
    return {"success": True, "documents": docs}


def search_kb_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    store = SQLiteStore(config)
    chunks = store.get_chunks(args.get("collection"))
    top_k = int(args.get("top_k") or config["retrieval"]["top_k"])
    mode = args.get("mode") or config["retrieval"]["default_mode"]
    embedder = build_embedding_client(config) if mode != "keyword" else None
    semantic_results = None
    if embedder is not None and chroma_enabled(config):
        semantic_results = search_chroma(config, args.get("collection"), embedder.embed_query(args["query"]), top_k * 2)
    results = search_chunks(
        chunks,
        args["query"],
        mode=mode,
        top_k=top_k,
        bm25_weight=float(config["retrieval"]["bm25_weight"]),
        vector_weight=float(config["retrieval"]["vector_weight"]),
        embedding_dim=int(config["embedding"]["dimension"]),
        embedder=embedder,
        semantic_results=semantic_results,
    )
    public_results = [_public_chunk(r) for r in results]
    log_event(
        config,
        "rag_queries.jsonl",
        {
            "query": args["query"],
            "collection": args.get("collection"),
            "retrieval_mode": mode,
            "top_k": top_k,
            "retrieved_chunks": [r["chunk_id"] for r in public_results],
            "scores": [r.get("score") for r in public_results],
            "success": True,
        },
    )
    return {"success": True, "query": args["query"], "results": public_results}


def ask_kb_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    search = search_kb_tool(config, args)
    answer = generate_grounded_answer(args["query"], search["results"], float(config["retrieval"]["min_confidence"]), config)
    return {"success": True, **answer}


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
