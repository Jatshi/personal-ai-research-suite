from __future__ import annotations

import math

from src.evaluation.metrics import compute_rag_metrics
from src.evaluation.ragas_evaluator import normalize_ragas_metrics
from src.config.config_loader import load_config
from src.evaluation.agent_evaluator import eval_agent


def test_eval_metrics():
    metrics = compute_rag_metrics([{"source_hit": True, "citations": ["c"], "should_answer": True, "refused": False, "keyword_coverage": 1, "confidence": 0.8}])
    assert metrics["retrieval_hit_rate"] == 1.0


def test_agent_eval_reads_dataset():
    report = eval_agent(load_config(), "examples/sample_eval/agent_eval.jsonl")
    assert report["metrics"]["case_count"] == 1
    assert report["metrics"]["success_rate"] == 1.0


def test_ragas_metric_normalization_preserves_finite_values_and_replaces_nan():
    metrics, undefined = normalize_ragas_metrics({"faithfulness": 0.8, "context_recall": math.nan})
    assert metrics == {"faithfulness": 0.8, "context_recall": None}
    assert undefined == ["context_recall"]
