from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

from src.agents.personal_assistant_agent import PersonalAssistantAgent
from src.config.config_loader import load_config
from src.evaluation.agent_evaluator import eval_agent
from src.evaluation.rag_evaluator import eval_rag
from src.mcp.mcp_server import serve_legacy_json_stdio, serve_stdio
from src.observability.trace_logger import JsonlLogger
from src.reading.article_extractor import import_reading_path, import_reading_url
from src.reading.reading_tools import reading_list_markdown, reading_search
from src.tools.default_registry import build_registry
from src.tools.kb_tools import ingest_tool, list_docs_tool


def main() -> None:
    parser = argparse.ArgumentParser(description="personal-ai-workspace CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest")
    p.add_argument("--path", required=True)
    p.add_argument("--collection", default="personal")

    p = sub.add_parser("list-docs")
    p.add_argument("--collection")

    p = sub.add_parser("reindex")
    p.add_argument("--collection", default="personal")

    p = sub.add_parser("delete-doc")
    p.add_argument("--doc-id", required=True)
    p.add_argument("--confirm", action="store_true", help="Actually delete the document and its chunks. Default is dry-run.")

    p = sub.add_parser("show-doc")
    p.add_argument("--doc-id", required=True)

    p = sub.add_parser("search")
    p.add_argument("--query", required=True)
    p.add_argument("--collection")
    p.add_argument("--mode", default="hybrid")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--query-rewrite", choices=["none", "hyde", "decomposition"])
    p.add_argument("--crag", action="store_true")
    p.add_argument("--multi-hop", action="store_true")

    p = sub.add_parser("ask")
    p.add_argument("--query", required=True)
    p.add_argument("--collection")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--query-rewrite", choices=["none", "hyde", "decomposition"])
    p.add_argument("--crag", action="store_true")
    p.add_argument("--multi-hop", action="store_true")

    p = sub.add_parser("agent")
    p.add_argument("--goal", required=True)
    p.add_argument("--mode", choices=["planner", "react"])
    p.add_argument("--session-id", default="default")

    p = sub.add_parser("daily-report")
    p.add_argument("--date", default="")
    p.add_argument("--collection", default="notes")
    p.add_argument("--todo", default="todo.md")

    p = sub.add_parser("weekly-report")
    p.add_argument("--from", dest="date_from", default="")
    p.add_argument("--to", dest="date_to", default="")
    p.add_argument("--collection", default="notes")
    p.add_argument("--todo", default="todo.md")

    p = sub.add_parser("import-url")
    p.add_argument("--url", required=True)
    p.add_argument("--collection", default="reading")

    p = sub.add_parser("import-reading")
    p.add_argument("--path", required=True)
    p.add_argument("--collection", default="reading")

    p = sub.add_parser("reading-search")
    p.add_argument("--query", required=True)
    p.add_argument("--collection", default="reading")

    p = sub.add_parser("reading-list")
    p.add_argument("--topic", required=True)
    p.add_argument("--output")

    p = sub.add_parser("eval-rag")
    p.add_argument("--dataset", required=True)
    p.add_argument("--output")
    p.add_argument("--engine", choices=["builtin", "ragas"], default="builtin")

    p = sub.add_parser("eval-ab")
    p.add_argument("--dataset", required=True)
    p.add_argument("--config-a", required=True, help="JSON object with config overrides")
    p.add_argument("--config-b", required=True, help="JSON object with config overrides")

    p = sub.add_parser("eval-agent")
    p.add_argument("--dataset")
    p.add_argument("--output")
    sub.add_parser("mcp-serve")
    sub.add_parser("mcp-legacy-serve", help="Compatibility-only JSON-lines MCP diagnostic server.")

    p = sub.add_parser("mcp-client")
    p.add_argument("--tool", required=True)
    p.add_argument("--args", default="{}")

    p = sub.add_parser("doctor-llm")
    p.add_argument("--call-api", action="store_true", help="Send a minimal real API request.")

    sub.add_parser("doctor-config")

    sub.add_parser("show-logs")

    args = parser.parse_args()
    config = load_config()
    registry = build_registry(config)

    if args.command == "ingest":
        print_json(ingest_tool(config, {"path": args.path, "collection": args.collection}))
    elif args.command == "list-docs":
        print_json(list_docs_tool(config, {"collection": args.collection}))
    elif args.command == "reindex":
        from src.indexing.index_manager import ingest_path
        from src.indexing.chroma_store import delete_chroma_collection
        from src.storage.sqlite_store import SQLiteStore

        store = SQLiteStore(config)
        docs = store.list_documents(args.collection)
        paths = sorted({d["file_path"] for d in docs if d.get("file_path")})
        store.delete_collection(args.collection)
        delete_chroma_collection(config, args.collection)
        reindexed = []
        for path in paths:
            if Path(path).exists():
                reindexed.extend(ingest_path(config, path, args.collection))
        print_json({"success": True, "collection": args.collection, "source_documents": len(paths), "reindexed_documents": len(reindexed)})
    elif args.command == "delete-doc":
        from src.indexing.chroma_store import delete_chroma_ids
        from src.storage.sqlite_store import SQLiteStore

        store = SQLiteStore(config)
        chunks = [c for c in store.get_chunks() if c.get("doc_id") == args.doc_id]
        collection = chunks[0].get("collection") if chunks else None
        plan = {"operation": "delete_doc", "doc_id": args.doc_id, "chunk_count": len(chunks), "collection": collection, "confirm": args.confirm}
        if not args.confirm:
            print_json({"success": True, "executed": False, "requires_confirmation": True, "plan": plan})
        else:
            delete_chroma_ids(config, collection, [c["chunk_id"] for c in chunks])
            store.delete_document(args.doc_id)
            print_json({"success": True, "executed": True, "deleted": args.doc_id, "plan": plan})
    elif args.command == "show-doc":
        docs = [d for d in list_docs_tool(config, {})["documents"] if d["doc_id"] == args.doc_id]
        print_json({"success": bool(docs), "document": docs[0] if docs else None})
    elif args.command == "search":
        print_json(registry.call("search_kb", _retrieval_args(args)))
    elif args.command == "ask":
        print_json(registry.call("ask_kb", _retrieval_args(args)))
    elif args.command == "agent":
        if args.mode == "react":
            from src.agents.react_agent import ReActAgent

            print_json(ReActAgent(registry).run(args.goal, args.session_id))
        else:
            print_json(PersonalAssistantAgent(registry).run(args.goal))
    elif args.command == "daily-report":
        print(registry.call("generate_daily_report", {"date": args.date, "collection": args.collection, "todo": args.todo})["report"])
    elif args.command == "weekly-report":
        print(registry.call("generate_weekly_report", {"from": args.date_from, "to": args.date_to, "collection": args.collection, "todo": args.todo})["report"])
    elif args.command == "import-url":
        print_json({"success": True, "item": import_reading_url(config, args.url, args.collection)})
    elif args.command == "import-reading":
        print_json({"success": True, "items": import_reading_path(config, args.path, args.collection)})
    elif args.command == "reading-search":
        print_json({"success": True, "results": reading_search(config, args.query, args.collection)})
    elif args.command == "reading-list":
        print(reading_list_markdown(config, args.topic, args.output))
    elif args.command == "eval-rag":
        if args.engine == "ragas":
            from src.evaluation.ragas_evaluator import eval_ragas

            print_json(eval_ragas(config, args.dataset))
        else:
            print_json(eval_rag(config, args.dataset, args.output))
    elif args.command == "eval-ab":
        from src.evaluation.ab_testing import compare_configs

        print_json(compare_configs(config, args.dataset, parse_args_json(args.config_a), parse_args_json(args.config_b)))
    elif args.command == "eval-agent":
        print_json(eval_agent(config, args.dataset, args.output))
    elif args.command == "mcp-serve":
        serve_stdio(config)
    elif args.command == "mcp-legacy-serve":
        serve_legacy_json_stdio(config)
    elif args.command == "mcp-client":
        print_json(registry.call(args.tool, parse_args_json(args.args)))
    elif args.command == "doctor-llm":
        print_json(doctor_llm(config, call_api=args.call_api))
    elif args.command == "doctor-config":
        print_json(doctor_config(config))
    elif args.command == "show-logs":
        print_json(
            {
                "rag_queries": JsonlLogger(config, "rag_queries.jsonl").tail(20),
                "tool_calls": JsonlLogger(config, "tool_calls.jsonl").tail(20),
                "audit": JsonlLogger(config, "audit_log.jsonl").tail(20),
                "errors": JsonlLogger(config, "errors.jsonl").tail(20),
            }
        )


def print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _retrieval_args(args) -> dict:
    return {
        "query": args.query,
        "collection": args.collection,
        "mode": getattr(args, "mode", None) or "hybrid",
        "top_k": args.top_k,
        "query_rewrite": getattr(args, "query_rewrite", None),
        "crag_enabled": True if getattr(args, "crag", False) else None,
        "multi_hop_enabled": True if getattr(args, "multi_hop", False) else None,
    }


def parse_args_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(text)
            return value if isinstance(value, dict) else {}
        except Exception:
            pass
    repaired = text.strip()
    if repaired.startswith("{") and repaired.endswith("}") and ":" in repaired:
        body = repaired[1:-1]
        parsed: dict[str, str] = {}
        for part in body.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            parsed[key.strip().strip("'\"")] = value.strip().strip("'\"")
        if parsed:
            return parsed
    raise ValueError(f"Invalid JSON args: {text}")


def doctor_llm(config: dict, call_api: bool = False) -> dict:
    return _doctor_llm_impl(config, call_api=call_api)


def doctor_config(config: dict) -> dict:
    import importlib.util
    import os

    from src.config.config_loader import resolve_project_path

    required = ["app", "server", "chunking", "retrieval", "embedding", "llm", "agent", "safety", "observability"]
    errors: list[str] = []
    warnings: list[str] = []
    for key in required:
        if key not in config:
            errors.append(f"Missing required config section: {key}")

    data_dir = resolve_project_path(config, config.get("app", {}).get("data_dir", "./data"))
    log_dir = resolve_project_path(config, config.get("observability", {}).get("log_dir", "./data/logs"))
    vector_dir = resolve_project_path(config, config.get("vector_store", {}).get("persist_dir", "./data/indexes/chroma"))
    writable = {str(p): _ensure_writable_dir(p) for p in [data_dir, log_dir, vector_dir]}
    for path, ok in writable.items():
        if not ok:
            errors.append(f"Directory is not writable: {path}")

    if config.get("server", {}).get("api_auth_enabled") and not os.getenv(config.get("server", {}).get("api_token_env", "PERSONAL_AI_API_TOKEN")):
        errors.append("API auth is enabled but the configured API token environment variable is not set.")
    if config.get("llm", {}).get("backend") != "mock" and not os.getenv(config.get("llm", {}).get("api_key_env", "OPENAI_API_KEY")):
        errors.append("Non-mock LLM backend is configured but the LLM API key environment variable is not set.")
    if config.get("embedding", {}).get("backend") != "mock" and not os.getenv(config.get("embedding", {}).get("api_key_env", "OPENAI_API_KEY")):
        errors.append("Non-mock embedding backend is configured but the embedding API key environment variable is not set.")
    if config.get("vector_store", {}).get("backend") == "chroma" and importlib.util.find_spec("chromadb") is None:
        errors.append("Chroma backend is configured but chromadb is not installed.")
    if not config.get("safety", {}).get("require_dry_run_for_write", True):
        warnings.append("require_dry_run_for_write is disabled.")
    if not config.get("safety", {}).get("block_sensitive_files", True):
        warnings.append("block_sensitive_files is disabled.")
    return {
        "success": not errors,
        "config_path": config.get("_config_path", ""),
        "errors": errors,
        "warnings": warnings,
        "writable_dirs": writable,
        "mode": "production" if not config.get("app", {}).get("mock_mode", True) else "mock",
    }


def _doctor_llm_impl(config: dict, call_api: bool = False) -> dict:
    import importlib.util
    import os

    from src.generation.factory import build_embedding_client, build_llm_client

    llm_cfg = config.get("llm", {})
    emb_cfg = config.get("embedding", {})
    vector_cfg = config.get("vector_store", {})
    result = {
        "success": True,
        "config_path": config.get("_config_path", ""),
        "llm_backend": llm_cfg.get("backend", "mock"),
        "embedding_backend": emb_cfg.get("backend", "mock"),
        "vector_store_backend": vector_cfg.get("backend", "sqlite"),
        "vector_store_persist_dir": vector_cfg.get("persist_dir", "./data/indexes/chroma"),
        "openai_package_installed": importlib.util.find_spec("openai") is not None,
        "chromadb_package_installed": importlib.util.find_spec("chromadb") is not None,
        "llm_api_key_env": llm_cfg.get("api_key_env", "OPENAI_API_KEY"),
        "llm_api_key_present": bool(os.getenv(llm_cfg.get("api_key_env", "OPENAI_API_KEY"))),
        "embedding_api_key_env": emb_cfg.get("api_key_env", "OPENAI_API_KEY"),
        "embedding_api_key_present": bool(os.getenv(emb_cfg.get("api_key_env", "OPENAI_API_KEY"))),
        "api_checked": False,
        "errors": [],
    }
    try:
        llm = build_llm_client(config)
        result["llm_client"] = llm.__class__.__name__
    except Exception as exc:
        result["success"] = False
        result["errors"].append(f"llm: {exc}")
    try:
        emb = build_embedding_client(config)
        result["embedding_client"] = emb.__class__.__name__
    except Exception as exc:
        result["success"] = False
        result["errors"].append(f"embedding: {exc}")
    if call_api and result["success"]:
        result["api_checked"] = True
        try:
            result["llm_sample"] = build_llm_client(config).generate("Reply with OK.", [])[:200]
            result["embedding_sample_dimension"] = len(build_embedding_client(config).embed_query("test"))
        except Exception as exc:
            result["success"] = False
            result["errors"].append(f"api_call: {exc}")
    return result


def _ensure_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
