from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agents.personal_assistant_agent import PersonalAssistantAgent
from src.tools.default_registry import build_registry


def eval_agent(config: dict[str, Any], dataset: str | None = None, output: str | None = None) -> dict[str, Any]:
    dataset_path = Path(dataset or "./examples/sample_eval/agent_eval.jsonl")
    if not dataset_path.is_absolute():
        dataset_path = Path(config["_project_root"]) / dataset_path
    records = []
    registry = build_registry(config)
    agent = PersonalAssistantAgent(registry)
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        result = agent.run(item["goal"])
        expected_tools = set(item.get("expected_tools", []))
        used_tools = {
            step.get("tool_name") or step.get("name")
            for step in result.get("steps", [])
            if isinstance(step, dict) and (step.get("tool_name") or step.get("name"))
        }
        # Current registry outputs do not include the tool name in nested results, so infer
        # from expected observable fields as a stable compatibility path.
        if any("results" in step for step in result.get("steps", []) if isinstance(step, dict)):
            used_tools.add("search_kb")
        if any("report" in step for step in result.get("steps", []) if isinstance(step, dict)):
            used_tools.add("generate_weekly_report")
        records.append(
            {
                "goal": item["goal"],
                "success": bool(result.get("success")),
                "expected_tools": sorted(expected_tools),
                "used_tools": sorted(used_tools),
                "tool_coverage": len(expected_tools & used_tools) / max(len(expected_tools), 1),
                "requires_confirmation_expected": bool(item.get("should_require_confirmation", False)),
                "requires_confirmation_observed": _requires_confirmation(result),
            }
        )
    metrics = {
        "case_count": len(records),
        "success_rate": _avg([1.0 if r["success"] else 0.0 for r in records]),
        "tool_coverage": _avg([r["tool_coverage"] for r in records]),
        "confirmation_policy_accuracy": _avg(
            [1.0 if r["requires_confirmation_expected"] == r["requires_confirmation_observed"] else 0.0 for r in records]
        ),
    }
    report = {"metrics": metrics, "records": records}
    if output:
        out = Path(output)
        if not out.is_absolute():
            out = Path(config["_project_root"]) / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# Agent Evaluation Report\n\n```json\n" + json.dumps(report, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    return report


def _requires_confirmation(result: dict[str, Any]) -> bool:
    stack: list[Any] = [result]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if item.get("requires_confirmation") is True:
                return True
            error = str(item.get("error", "")).lower()
            if "requires confirmation" in error or "confirm=true required" in error:
                return True
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return False


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0
