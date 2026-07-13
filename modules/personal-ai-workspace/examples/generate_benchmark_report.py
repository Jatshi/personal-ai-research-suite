from __future__ import annotations

"""Generate a portfolio-ready Markdown report from run_benchmark.py JSON."""

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def value(value: Any) -> str:
    return "-" if value is None else f"{float(value):.3f}"


def best_variant(results: dict[str, Any], metric: str, source: str = "metrics") -> str | None:
    candidates: list[tuple[float, str]] = []
    for name, result in results["variants"].items():
        metrics = result.get(source, {}).get("metrics", {}) if source == "ragas" else result.get("metrics", {})
        score = metrics.get(metric)
        if isinstance(score, (int, float)):
            candidates.append((float(score), name))
    return max(candidates)[1] if candidates else None


def render_report(results: dict[str, Any]) -> str:
    variants = results["variants"]
    production_ragas = any(result.get("ragas", {}).get("status") == "ok" for result in variants.values())
    mode_notice = (
        "RAGAS was executed against a configured production evaluator."
        if production_ragas
        else "Offline/mock baseline: RAGAS was not executed. Run with `--config config.production.yaml --ragas` before using numerical claims in a resume."
    )
    lines = [
        "# ScholarMind RAG Benchmark Report",
        "",
        "> Reproducible benchmark over public AI paper fact cards. Replace the default corpus with a reviewed local paper directory before making domain-specific performance claims.",
        f"> **Evaluation mode:** {mode_notice}",
        "",
        "## Protocol",
        "",
        f"- Cases: {sum(results['category_counts'].values())} ({', '.join(f'{key}={value}' for key, value in results['category_counts'].items())})",
        "- Variants: Base hybrid RAG, CRAG routing, HyDE query rewrite, Hybrid + GraphRAG.",
        "- Deterministic metrics: source hit, citation presence, refusal accuracy, keyword coverage, confidence, and latency.",
        "- RAGAS is optional because it requires a configured evaluator model; out-of-scope cases are evaluated by refusal accuracy rather than answer-quality metrics.",
        "",
        "## Overall Comparison",
        "",
        "| Variant | Source hit | Expected-source recall | Citation | Refusal | Keyword coverage | Avg confidence | Avg latency (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in variants.items():
        metrics = result["metrics"]
        lines.append(f"| {name} | {value(metrics.get('retrieval_hit_rate'))} | {value(metrics.get('expected_source_recall'))} | {value(metrics.get('citation_presence'))} | {value(metrics.get('refusal_accuracy'))} | {value(metrics.get('answer_keyword_coverage'))} | {value(metrics.get('average_confidence'))} | {value(result.get('average_latency_ms'))} |")

    lines.extend(["", "## Refusal Accuracy Chart", "", "```mermaid", "xychart-beta", '    title "Refusal Accuracy by Variant"', "    x-axis [" + ", ".join(f'"{name}"' for name in variants) + "]", "    y-axis " + '"accuracy" 0 --> 1', "    bar [" + ", ".join(value(result["metrics"].get("refusal_accuracy")) for result in variants.values()) + "]", "```"])
    for category in results["category_counts"]:
        lines.extend(["", f"## Category: {category}", "", "| Variant | Source hit | Expected-source recall | Citation | Refusal | Keyword coverage |", "|---|---:|---:|---:|---:|---:|"])
        for name, result in variants.items():
            metrics = result["metrics_by_category"].get(category, {})
            lines.append(f"| {name} | {value(metrics.get('retrieval_hit_rate'))} | {value(metrics.get('expected_source_recall'))} | {value(metrics.get('citation_presence'))} | {value(metrics.get('refusal_accuracy'))} | {value(metrics.get('answer_keyword_coverage'))} |")

    lines.extend(["", "## RAGAS", "", "| Variant | Status | Faithfulness | Answer relevancy | Context precision | Context recall |", "|---|---|---:|---:|---:|---:|"])
    for name, result in variants.items():
        ragas = result.get("ragas", {})
        metrics = ragas.get("metrics", {})
        lines.append(f"| {name} | {ragas.get('status', 'unknown')} | {value(metrics.get('faithfulness'))} | {value(metrics.get('answer_relevancy'))} | {value(metrics.get('context_precision'))} | {value(metrics.get('context_recall'))} |")

    findings = [
        f"Best deterministic source-hit variant: `{best_variant(results, 'retrieval_hit_rate') or 'not available'}`.",
        f"Best refusal-accuracy variant: `{best_variant(results, 'refusal_accuracy') or 'not available'}`.",
    ]
    ragas_best = best_variant(results, "faithfulness", "ragas")
    findings.append(f"Best RAGAS faithfulness variant: `{ragas_best}`." if ragas_best else "RAGAS was not available; configure an OpenAI-compatible evaluator and rerun with `--ragas`.")
    lines.extend(["", "## Key Findings", "", *[f"- {finding}" for finding in findings], "", "## Resume-Safe Interpretation", "", "This report demonstrates a reproducible evaluation harness, not a universal claim that one retrieval strategy always wins. Report the corpus, model, configuration, latency, and refusal behavior together; rerun on your own reviewed paper set before citing numbers in a resume or interview.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Markdown benchmark report.")
    parser.add_argument("--input", type=Path, required=True, help="JSON output created by run_benchmark.py")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "docs" / "BENCHMARK_REPORT.md")
    args = parser.parse_args()
    results = json.loads(args.input.read_text(encoding="utf-8"))
    report = render_report(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote benchmark report: {args.output}")


if __name__ == "__main__":
    main()
