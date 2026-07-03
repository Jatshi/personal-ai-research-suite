from __future__ import annotations

import json
import re
from typing import Any

from src.llm.base import BaseLLMClient
from src.tools.tool_registry import ToolRegistry, ToolSpec


def plan_agent_task(goal: str) -> dict[str, Any]:
    text = goal.lower()
    steps: list[dict[str, Any]] = []
    if any(token in text for token in ["整理", "organize", "rename", "重命名", "文件"]):
        path = _extract_path(goal) or "messy_files"
        steps.append({"tool": "organize_files", "params": {"path": path}, "dry_run": True, "risk": "medium"})
    if any(token in text for token in ["扫描", "scan"]):
        path = _extract_path(goal) or "messy_files"
        steps.append({"tool": "scan_folder", "params": {"path": path}, "dry_run": False, "risk": "low"})
    if any(token in text for token in ["论文检查", "博士", "thesis", "图表", "参考文献"]):
        path = _extract_path(goal) or "thesis_sample/thesis.md"
        steps.append({"tool": "check_thesis", "params": {"path": path}, "dry_run": False, "risk": "low"})
    if any(token in text for token in ["读论文", "阅读论文", "paper", "literature"]):
        path = _extract_path(goal) or "papers"
        steps.append({"tool": "read_papers", "params": {"path": path, "output": "./data/exports/paper_notes"}, "dry_run": False, "risk": "low"})
    if any(token in text for token in ["日报", "daily"]):
        steps.append({"tool": "generate_daily_report", "params": {"todo_path": "./workspace/todo.md"}, "dry_run": False, "risk": "low"})
    if any(token in text for token in ["周报", "weekly"]):
        steps.append({"tool": "generate_weekly_report", "params": {"todo_path": "./workspace/todo.md"}, "dry_run": False, "risk": "low"})
    if any(token in text for token in ["知识库", "rag", "检索", "搜索"]):
        steps.append({"tool": "search_knowledge_base", "params": {"query": goal}, "dry_run": False, "risk": "low"})
    if not steps:
        steps.append({"tool": "generate_todo_list", "params": {"goal": goal}, "dry_run": False, "risk": "low"})
    return _finalize_plan(goal, steps, mode="rule")


def plan_agent_task_with_llm(goal: str, registry: ToolRegistry, llm: BaseLLMClient | None = None) -> dict[str, Any]:
    if llm is None:
        return plan_agent_task(goal)
    tool_specs = [_tool_spec_for_prompt(spec) for spec in registry.specs() if spec.name != "plan_agent_task"]
    prompt = (
        "You are a local AI agent planner. Convert the user goal into a JSON tool plan.\n"
        "Use only tools from the provided tool list. Do not invent tools or parameters.\n"
        "For medium/high risk tools, set dry_run=true unless the user explicitly asks to execute and confirms.\n"
        "Return JSON only with this shape:\n"
        '{"goal": "...", "steps": [{"tool": "tool_name", "params": {}, "dry_run": true, "reason": "..."}]}\n'
        f"User goal: {goal}"
    )
    try:
        raw = llm.generate(prompt, context=[{"text": json.dumps({"tools": tool_specs}, ensure_ascii=False)}])
        candidate = _extract_json_object(raw)
        return validate_plan(candidate, goal, registry, fallback=plan_agent_task(goal), mode="llm")
    except Exception as exc:
        fallback = plan_agent_task(goal)
        fallback["planner_error"] = str(exc)
        return fallback


def validate_plan(candidate: dict[str, Any], goal: str, registry: ToolRegistry, fallback: dict[str, Any], mode: str) -> dict[str, Any]:
    specs = {spec.name: spec for spec in registry.specs()}
    raw_steps = candidate.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        return fallback | {"planner_error": "LLM returned no steps"}
    steps: list[dict[str, Any]] = []
    for raw in raw_steps:
        if not isinstance(raw, dict):
            continue
        tool = raw.get("tool")
        if tool not in specs or tool == "plan_agent_task":
            continue
        params = raw.get("params") if isinstance(raw.get("params"), dict) else {}
        spec = specs[tool]
        required = spec.input_schema.get("required", [])
        if any(key not in params for key in required):
            continue
        risk = spec.risk_level
        dry_run = bool(raw.get("dry_run", risk in {"medium", "high"}))
        if risk in {"medium", "high"}:
            dry_run = True
        steps.append({"tool": tool, "params": params, "dry_run": dry_run, "risk": risk, "reason": str(raw.get("reason", ""))})
    if not steps:
        return fallback | {"planner_error": "LLM plan failed validation"}
    return _finalize_plan(goal, steps, mode=mode)


def run_agent_plan(
    goal: str,
    registry: ToolRegistry,
    execute: bool = False,
    confirmed: bool = False,
    llm: BaseLLMClient | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    plan = plan_agent_task_with_llm(goal, registry, llm) if use_llm else plan_agent_task(goal)
    results = []
    for step in plan["steps"]:
        dry_run = bool(step.get("dry_run", False))
        if step["risk"] in {"medium", "high"}:
            dry_run = not (execute and confirmed)
        result = registry.call(step["tool"], step["params"], dry_run=dry_run, confirmed=confirmed)
        results.append({"step": step, "result": result.__dict__})
    return {"plan": plan, "executed": execute, "confirmed": confirmed, "planner": plan.get("planner", "rule"), "results": results}


def _finalize_plan(goal: str, steps: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    return {"goal": goal, "planner": mode, "steps": steps, "requires_confirmation": any(s["risk"] in {"medium", "high"} for s in steps)}


def _tool_spec_for_prompt(spec: ToolSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "description": spec.description,
        "input_schema": spec.input_schema,
        "risk_level": spec.risk_level,
        "requires_confirmation": spec.requires_confirmation,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Planner output must be a JSON object")
    return value


def _extract_path(goal: str) -> str | None:
    markers = ["path=", "路径=", "--path "]
    for marker in markers:
        if marker in goal:
            tail = goal.split(marker, 1)[1].strip()
            return tail.split()[0].strip('"').strip("'")
    return None
