from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.indexing.index_manager import IndexManager

REFUSAL_PREFIX = "知识库中没有足够证据"


def run_rag_eval(manager: IndexManager, dataset: str | Path, output: str | Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in Path(dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    total = len(rows)
    retrieval_hits = 0
    citation_present = 0
    sufficiency_correct = 0
    refusal_correct = 0
    confidences: list[float] = []
    details = []
    for row in rows:
        query = row["query"]
        expected_doc = row.get("expected_doc")
        should_answer = bool(row.get("should_answer", True))
        answer = manager.ask(query, row.get("collection"), row.get("mode", "hybrid"), int(row.get("top_k", 5)))
        hit = any(expected_doc in r.chunk.metadata.get("filename", "") for r in answer.evidence) if expected_doc else bool(answer.evidence)
        refused = answer.text.strip().startswith(REFUSAL_PREFIX)
        has_citation = bool(answer.citations)
        retrieval_hits += int(hit)
        citation_present += int(has_citation if should_answer else True)
        sufficiency_correct += int((not refused) == should_answer)
        refusal_correct += int(refused) if not should_answer else 0
        confidences.append(answer.confidence)
        details.append(
            {
                "query": query,
                "hit": hit,
                "should_answer": should_answer,
                "refused": refused,
                "confidence": answer.confidence,
                "citations": answer.citations,
            }
        )
    metrics = {
        "total": total,
        "retrieval_hit_rate": round(retrieval_hits / total, 3) if total else 0.0,
        "citation_presence": round(citation_present / total, 3) if total else 0.0,
        "evidence_sufficiency_accuracy": round(sufficiency_correct / total, 3) if total else 0.0,
        "refusal_when_no_evidence": round(refusal_correct / max(1, sum(not bool(r.get("should_answer", True)) for r in rows)), 3),
        "average_confidence": round(sum(confidences) / total, 3) if total else 0.0,
    }
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# RAG Evaluation Report", "", "## Metrics"]
    lines.extend(f"- {k}: {v}" for k, v in metrics.items())
    lines += ["", "## Details"]
    for item in details:
        lines.append(f"- query={item['query']} hit={item['hit']} refused={item['refused']} confidence={item['confidence']}")
    out.write_text("\n".join(lines), encoding="utf-8")
    return {"metrics": metrics, "details": details, "output": str(out)}

