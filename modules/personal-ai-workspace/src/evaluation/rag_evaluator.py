from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.evaluation.metrics import compute_rag_metrics
from src.grounding.evidence_checker import NO_EVIDENCE
from src.tools.kb_tools import ask_kb_tool
from src.utils.text_utils import tokenize


def eval_rag(config: dict[str, Any], dataset: str, output: str | None = None) -> dict[str, Any]:
    records = []
    for line in Path(dataset).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        started = time.perf_counter()
        answer = ask_kb_tool(config, {"query": item["question"], "collection": item.get("collection"), "top_k": 5})
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        evidence = answer.get("evidence", [])
        expected_sources = set(item.get("expected_sources", []))
        got_sources = {e.get("file_name") for e in evidence}
        expected_keywords = set(item.get("expected_keywords", []))
        ans_tokens = set(tokenize(answer.get("answer", "")))
        trace = answer.get("retrieval_trace", {})
        route = (trace.get("route") or {}).get("route")
        compression = trace.get("compression") or {}
        records.append(
            {
                "question": item["question"],
                "should_answer": item.get("should_answer", True),
                "source_hit": not expected_sources or bool(expected_sources & got_sources),
                "expected_source_recall": len(expected_sources & got_sources) / max(len(expected_sources), 1) if item.get("should_answer", True) else 1.0,
                "citations": answer.get("citations", []),
                "refused": NO_EVIDENCE in answer.get("answer", ""),
                "keyword_coverage": len(expected_keywords & ans_tokens) / max(len(expected_keywords), 1),
                "confidence": answer.get("confidence", 0.0),
                "expected_route": item.get("expected_route"),
                "actual_route": route,
                "compression_ratio": float(compression.get("after_chars", 0)) / max(float(compression.get("before_chars", 0)), 1.0),
                "citation_retained": bool(answer.get("citations")) if evidence else True,
                "latency_ms": latency_ms,
            }
        )
    metrics = compute_rag_metrics(records)
    report = {"metrics": metrics, "records": records}
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# RAG Evaluation Report\n\n```json\n" + json.dumps(report, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    return report
