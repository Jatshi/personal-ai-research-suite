from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from src.academic.literature_table import LiteratureTableGenerator
from src.academic.paper_note_generator import PaperNoteGenerator
from src.config.config_loader import load_config, project_path
from src.grounding.citation_builder import build_citations
from src.indexing.index_manager import IndexManager
from src.evaluation import run_rag_eval
from src.corpus.bulk_import import cleanup_duplicate_documents, ingest_real_corpus, reclassify_index_metadata, scan_real_corpus


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Personal Academic RAG Workspace")
    sub = p.add_subparsers(dest="cmd", required=True)
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--path", required=True)
    ingest.add_argument("--collection", default="personal")
    ingest.add_argument("--tags", default="")
    ingest.add_argument("--doc-type", default="general")
    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--mode", default="hybrid", choices=["keyword", "semantic", "hybrid"])
    search.add_argument("--top-k", type=int, default=5)
    search.add_argument("--collection")
    ask = sub.add_parser("ask")
    ask.add_argument("--query", required=True)
    ask.add_argument("--collection")
    ask.add_argument("--mode", default="hybrid")
    ask.add_argument("--top-k", type=int, default=5)
    reindex = sub.add_parser("reindex")
    reindex.add_argument("--collection")
    delete = sub.add_parser("delete")
    delete.add_argument("--doc-id", required=True)
    export = sub.add_parser("export-notes")
    export.add_argument("--collection", default="academic")
    export.add_argument("--output", required=True)
    ev = sub.add_parser("eval")
    ev.add_argument("--dataset", required=True)
    ev.add_argument("--output", required=True)
    scan = sub.add_parser("scan-real-corpus")
    scan.add_argument("--root", required=True)
    scan.add_argument("--output", default="./data/exports/real_corpus_manifest.json")
    bulk = sub.add_parser("ingest-real-corpus")
    bulk.add_argument("--root", required=True)
    bulk.add_argument("--manifest-output", default="./data/exports/real_corpus_manifest.json")
    reclassify = sub.add_parser("reclassify-corpus")
    reclassify.add_argument("--root", required=True)
    sub.add_parser("cleanup-duplicates")
    sub.add_parser("doctor-config")
    doctor_llm = sub.add_parser("doctor-llm")
    doctor_llm.add_argument("--call-api", action="store_true", help="Make a real LLM and embedding API call.")
    return p


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    config = load_config()
    if args.cmd == "doctor-config":
        print_json(doctor_config(config))
        return
    if args.cmd == "doctor-llm":
        print_json(doctor_llm(config, call_api=args.call_api))
        return

    manager = IndexManager(config)
    if args.cmd == "ingest":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        doc_type = "paper" if args.collection == "academic" and args.doc_type == "general" else args.doc_type
        ids = manager.ingest_path(args.path, args.collection, tags=tags, doc_type=doc_type)
        print(f"Ingested {len(ids)} documents")
        for doc_id in ids:
            print(doc_id)
    elif args.cmd == "search":
        results = manager.search(args.query, args.mode, args.top_k, {"collection": args.collection} if args.collection else {})
        for i, r in enumerate(results, start=1):
            print(f"\n[{i}] score={r.score:.3f} bm25={r.bm25_score:.3f} vector={r.vector_score:.3f} chunk_id={r.chunk.chunk_id}")
            print(f"{r.chunk.metadata.get('filename')} page={r.chunk.metadata.get('page')} paragraph={r.chunk.metadata.get('paragraph')}")
            print(r.chunk.text[:600])
    elif args.cmd == "ask":
        answer = manager.ask(args.query, args.collection, args.mode, args.top_k)
        print(answer.text)
        print(f"\nconfidence={answer.confidence:.3f}")
        if answer.citations:
            print("\nCitations:")
            print("\n".join(answer.citations))
    elif args.cmd == "reindex":
        print(f"Reindexed {manager.reindex(args.collection)} chunks")
    elif args.cmd == "delete":
        print(f"Deleted {manager.delete_document(args.doc_id)} chunks")
    elif args.cmd == "export-notes":
        papers = manager.store.list_papers()
        out = Path(args.output)
        if not out.is_absolute():
            out = project_path(config, out)
        out.parent.mkdir(parents=True, exist_ok=True)
        content = ["# Academic Notes Export", "", LiteratureTableGenerator().generate(papers), ""]
        note_gen = PaperNoteGenerator()
        for paper in papers:
            chunks = manager.store.get_chunks_by_doc(paper["doc_id"])
            content.append(note_gen.generate(paper, paper.get("sections", {}), chunks))
        out.write_text("\n\n".join(content), encoding="utf-8")
        print(f"Exported notes to {out}")
    elif args.cmd == "eval":
        result = run_rag_eval(manager, args.dataset, args.output)
        print(f"Evaluation report: {result['output']}")
        print(result["metrics"])
    elif args.cmd == "scan-real-corpus":
        manifest = scan_real_corpus(args.root, project_path(config, args.output))
        print(f"Scanned {manifest['total_files']} files; unique={manifest['unique_files']} duplicates={manifest['duplicate_files']}")
        print(f"Manifest: {project_path(config, args.output)}")
    elif args.cmd == "ingest-real-corpus":
        summary = ingest_real_corpus(config, args.root, project_path(config, args.manifest_output))
        print(summary)
    elif args.cmd == "reclassify-corpus":
        print(reclassify_index_metadata(config, args.root))
    elif args.cmd == "cleanup-duplicates":
        print(cleanup_duplicate_documents(config))


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def doctor_config(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required_sections = ["app", "chunking", "retrieval", "embedding", "llm", "academic", "logging"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing config section: {section}")

    root = Path(config.get("_project_root", "."))
    workspace_dir = project_path(config, config.get("app", {}).get("workspace_dir", "./data"))
    try:
        workspace_dir.mkdir(parents=True, exist_ok=True)
        probe = workspace_dir / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except Exception as exc:
        errors.append(f"Workspace is not writable: {workspace_dir} ({exc})")

    if not (root / "requirements.txt").exists():
        errors.append("requirements.txt is missing.")
    if not (root / ".env.example").exists():
        warnings.append(".env.example is missing; users need a safe API-key template.")

    for section in ["embedding", "llm"]:
        backend = str(config.get(section, {}).get("backend", "mock")).lower()
        key_env = str(config.get(section, {}).get("api_key_env", "OPENAI_API_KEY"))
        if backend not in {"mock", "local_mock", "openai", "openai_compatible"}:
            errors.append(f"Unsupported {section}.backend: {backend}")
        if backend in {"openai", "openai_compatible"} and not os.getenv(key_env):
            errors.append(f"{section}.backend={backend} but environment variable {key_env} is not set.")

    try:
        import chromadb  # noqa: F401
    except Exception as exc:
        warnings.append(f"chromadb is unavailable; VectorStore will use JSON fallback. Detail: {exc}")

    return {
        "success": not errors,
        "config_path": config.get("_config_path"),
        "workspace_dir": str(workspace_dir),
        "embedding_backend": config.get("embedding", {}).get("backend", "mock"),
        "llm_backend": config.get("llm", {}).get("backend", "mock"),
        "errors": errors,
        "warnings": warnings,
    }


def doctor_llm(config: dict[str, Any], call_api: bool = False) -> dict[str, Any]:
    from src.generation.providers import build_embedding_client, build_llm_client

    result: dict[str, Any] = {
        "success": True,
        "call_api": call_api,
        "llm_backend": config.get("llm", {}).get("backend", "mock"),
        "embedding_backend": config.get("embedding", {}).get("backend", "mock"),
        "llm_model": config.get("llm", {}).get("model_name"),
        "embedding_model": config.get("embedding", {}).get("model_name"),
        "llm_api_key_env": config.get("llm", {}).get("api_key_env", "OPENAI_API_KEY"),
        "llm_api_key_present": bool(os.getenv(config.get("llm", {}).get("api_key_env", "OPENAI_API_KEY"))),
        "embedding_api_key_env": config.get("embedding", {}).get("api_key_env", "OPENAI_API_KEY"),
        "embedding_api_key_present": bool(os.getenv(config.get("embedding", {}).get("api_key_env", "OPENAI_API_KEY"))),
        "errors": [],
    }
    for section in ["llm", "embedding"]:
        backend = str(config.get(section, {}).get("backend", "mock")).lower()
        key_env = str(config.get(section, {}).get("api_key_env", "OPENAI_API_KEY"))
        if backend in {"openai", "openai_compatible"} and not os.getenv(key_env):
            result["success"] = False
            result["errors"].append(f"{section}: missing API key environment variable {key_env}")
    try:
        llm = build_llm_client(config)
        result["llm_client"] = llm.__class__.__name__
    except Exception as exc:
        result["success"] = False
        result["errors"].append(f"llm: {exc}")
    try:
        embedding = build_embedding_client(config)
        result["embedding_client"] = embedding.__class__.__name__
    except Exception as exc:
        result["success"] = False
        result["errors"].append(f"embedding: {exc}")

    if call_api and result["success"]:
        try:
            result["llm_sample"] = build_llm_client(config).generate("Reply with OK.", [])[:200]
            result["embedding_sample_dimension"] = len(build_embedding_client(config).embed_query("test"))
        except Exception as exc:
            result["success"] = False
            result["errors"].append(f"api_call: {exc}")
    return result


if __name__ == "__main__":
    main()
