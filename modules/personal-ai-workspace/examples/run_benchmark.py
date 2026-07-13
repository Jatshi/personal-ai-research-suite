from __future__ import annotations

"""Run reproducible retrieval benchmarks over paper cards or a local paper folder."""

import argparse
import copy
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.config_loader import load_config
from src.evaluation.metrics import compute_rag_metrics
from src.evaluation.rag_evaluator import eval_rag
from src.indexing.index_manager import ingest_path


VARIANTS: dict[str, dict[str, Any]] = {
    "base": {"retrieval": {"backend": "hybrid", "query_rewrite": "none", "crag_enabled": False, "multi_hop_enabled": False}},
    "crag": {"retrieval": {"backend": "hybrid", "query_rewrite": "none", "crag_enabled": True, "multi_hop_enabled": False}},
    "query_rewrite_hyde": {"retrieval": {"backend": "hybrid", "query_rewrite": "hyde", "crag_enabled": False, "multi_hop_enabled": False}},
    "graphrag": {"retrieval": {"backend": "hybrid+graphrag", "query_rewrite": "none", "crag_enabled": False, "multi_hop_enabled": False}, "graphrag": {"enabled": True, "backend": "networkx", "auto_index": True}},
}


def load_dataset(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def apply_overrides(config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(config)
    for section, values in overrides.items():
        result.setdefault(section, {}).update(values)
    return result


def category_metrics(records: list[dict[str, Any]], dataset: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record, item in zip(records, dataset, strict=True):
        categories[str(item["category"])].append(record)
    return {category: compute_rag_metrics(items) for category, items in sorted(categories.items())}


def run_variant(
    name: str,
    base_config: dict[str, Any],
    papers: Path,
    dataset_path: Path,
    dataset: list[dict[str, Any]],
    run_dir: Path,
    collection: str,
    enable_ragas: bool,
) -> dict[str, Any]:
    variant_dir = run_dir / name
    if variant_dir.exists():
        shutil.rmtree(variant_dir)
    config = apply_overrides(base_config, VARIANTS[name])
    config["app"]["data_dir"] = str(variant_dir / "data")
    config["vector_store"]["backend"] = "sqlite"
    config["evaluation"]["ragas_enabled"] = enable_ragas
    started = time.perf_counter()
    documents = ingest_path(config, str(papers), collection)
    report = eval_rag(config, str(dataset_path))
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    ragas: dict[str, Any] = {"status": "disabled"}
    if enable_ragas:
        try:
            from src.evaluation.ragas_evaluator import eval_ragas

            ragas = {"status": "ok", **eval_ragas(config, str(dataset_path))}
        except Exception as exc:  # Benchmark still records deterministic metrics offline.
            ragas = {"status": "unavailable", "error": str(exc)}
    records = report["records"]
    return {
        "variant": name,
        "configuration": VARIANTS[name],
        "indexed_documents": len(documents),
        "case_count": len(records),
        "metrics": report["metrics"],
        "metrics_by_category": category_metrics(records, dataset),
        "average_latency_ms": round(sum(float(item["latency_ms"]) for item in records) / max(len(records), 1), 3),
        "total_elapsed_ms": elapsed_ms,
        "ragas": ragas,
    }


def write_checkpoint(path: Path, results: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare ScholarMind RAG configurations on a paper corpus.")
    parser.add_argument("--papers", type=Path, default=PROJECT_ROOT / "examples" / "benchmark_papers")
    parser.add_argument("--dataset", type=Path, default=PROJECT_ROOT / "examples" / "benchmark_eval.jsonl")
    parser.add_argument("--config", default="config.yaml", help="Config path relative to the project root.")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data" / "exports" / "benchmark" / "benchmark_results.json")
    parser.add_argument("--collection", default="benchmark")
    parser.add_argument("--ragas", action="store_true", help="Run real-provider RAGAS metrics after deterministic evaluation.")
    parser.add_argument("--variants", nargs="+", choices=list(VARIANTS), default=list(VARIANTS), help="One or more variants to run; defaults to all four.")
    parser.add_argument("--resume", action="store_true", help="Reuse completed variants from an existing output JSON.")
    args = parser.parse_args()

    papers = args.papers.resolve()
    dataset_path = args.dataset.resolve()
    if not papers.is_dir() or not any(papers.iterdir()):
        raise SystemExit(f"Paper corpus directory is missing or empty: {papers}")
    dataset = load_dataset(dataset_path)
    if len(dataset) != 50:
        raise SystemExit(f"Expected exactly 50 benchmark cases, found {len(dataset)}.")

    base_config = load_config(args.config)
    if args.resume and args.output.exists():
        results = json.loads(args.output.read_text(encoding="utf-8"))
        results["ragas_requested"] = bool(results.get("ragas_requested") or args.ragas)
    else:
        results = {
            "schema_version": 1,
            "run_id": time.strftime("%Y%m%d-%H%M%S"),
            "dataset": str(dataset_path),
            "papers": str(papers),
            "category_counts": {category: sum(item["category"] == category for item in dataset) for category in ("simple", "complex", "multi_hop", "out_of_scope")},
            "ragas_requested": args.ragas,
            "variants": {},
        }
    run_dir = PROJECT_ROOT / "data" / "benchmark_runs" / str(results["run_id"])
    for name in args.variants:
        if args.resume and name in results["variants"]:
            print(f"Skipping completed benchmark variant: {name}", flush=True)
            continue
        print(f"Running benchmark variant: {name}", flush=True)
        results["variants"][name] = run_variant(name, base_config, papers, dataset_path, dataset, run_dir, args.collection, args.ragas)
        write_checkpoint(args.output, results)

    write_checkpoint(args.output, results)
    print(json.dumps({"success": True, "output": str(args.output), "variants": list(results["variants"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
