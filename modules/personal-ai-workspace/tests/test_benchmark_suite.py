from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_example_module(name: str):
    path = PROJECT_ROOT / "examples" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_benchmark_dataset_has_required_coverage():
    runner = _load_example_module("run_benchmark")
    rows = runner.load_dataset(PROJECT_ROOT / "examples" / "benchmark_eval.jsonl")
    assert len(rows) == 50
    assert Counter(row["category"] for row in rows) == {"simple": 15, "complex": 15, "multi_hop": 10, "out_of_scope": 10}
    assert all({"question", "expected_sources", "expected_keywords", "category", "should_answer", "reference_answer"} <= row.keys() for row in rows)
    corpus = PROJECT_ROOT / "examples" / "benchmark_papers"
    expected_sources = {source for row in rows for source in row["expected_sources"]}
    assert expected_sources <= {path.name for path in corpus.glob("*.md")}


def test_benchmark_report_includes_ragas_and_category_tables():
    report_module = _load_example_module("generate_benchmark_report")
    result = {
        "category_counts": {"simple": 1, "complex": 1, "multi_hop": 1, "out_of_scope": 1},
        "variants": {
            "base": {"metrics": {"retrieval_hit_rate": 0.5, "expected_source_recall": 0.5, "citation_presence": 1.0, "refusal_accuracy": 1.0, "answer_keyword_coverage": 0.5, "average_confidence": 0.5}, "average_latency_ms": 10, "metrics_by_category": {}, "ragas": {"status": "ok", "metrics": {"faithfulness": 0.8}}}
        },
    }
    text = report_module.render_report(result)
    assert "Expected-source recall" in text
    assert "## RAGAS" in text
    assert "## Category: multi_hop" in text
