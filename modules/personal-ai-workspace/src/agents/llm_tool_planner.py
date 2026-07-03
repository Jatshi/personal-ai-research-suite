from __future__ import annotations

import json
import re
from typing import Any

from src.generation.factory import build_llm_client
from src.tools.tool_registry import ToolRegistry


def build_tool_plan(registry: ToolRegistry, goal: str) -> dict[str, Any]:
    config = registry.config
    tools = registry.list_tools()
    prompt = _planner_prompt(goal, tools, int(config.get("agent", {}).get("max_steps", 8)))
    raw = build_llm_client(config).generate(prompt, [{"tools": tools, "goal": goal}])
    parsed = _parse_json(raw)
    calls = _sanitize_calls(parsed.get("tool_calls", []), tools, int(config.get("agent", {}).get("max_steps", 8)))
    if not calls:
        return fallback_tool_plan(goal)
    return {
        "plan": parsed.get("plan") or [f"Call {c['tool_name']}" for c in calls],
        "tool_calls": calls,
        "final_response_hint": parsed.get("final_response_hint", ""),
        "planner_backend": config.get("llm", {}).get("backend", "mock"),
        "raw_plan": raw,
    }


def fallback_tool_plan(goal: str) -> dict[str, Any]:
    return {
        "plan": ["Search the knowledge base.", "Generate a weekly report."],
        "tool_calls": [
            {"tool_name": "search_kb", "arguments": {"query": goal, "top_k": 3}},
            {"tool_name": "generate_weekly_report", "arguments": {"query": goal}},
        ],
        "final_response_hint": "Use tool outputs to summarize next actions.",
        "planner_backend": "fallback",
        "raw_plan": "",
    }


def _planner_prompt(goal: str, tools: list[dict[str, Any]], max_steps: int) -> str:
    compact_tools = [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("input_schema", {}),
            "risk_level": t.get("risk_level", "low"),
            "requires_confirmation": t.get("requires_confirmation", False),
        }
        for t in tools
    ]
    return (
        "You are a tool-planning AI agent. Return JSON only. Build a safe tool plan for the user goal.\n"
        "Do not invent tools. Do not request non-dry-run high-risk writes unless the user explicitly asked for execution.\n"
        f"Max tool calls: {max_steps}\n"
        f"Goal: {goal}\n"
        f"Available tools: {json.dumps(compact_tools, ensure_ascii=False)}\n"
        'Return schema: {"plan":["..."],"tool_calls":[{"tool_name":"...","arguments":{}}],"final_response_hint":"..."}'
    )


def _parse_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            return {}
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            return {}


def _sanitize_calls(calls: list[Any], tools: list[dict[str, Any]], max_steps: int) -> list[dict[str, Any]]:
    allowed = {t["name"]: t for t in tools}
    sanitized: list[dict[str, Any]] = []
    for call in calls[:max_steps]:
        if not isinstance(call, dict):
            continue
        name = call.get("tool_name") or call.get("name")
        if name not in allowed:
            continue
        args = call.get("arguments") or {}
        if not isinstance(args, dict):
            args = {}
        spec = allowed[name]
        if spec.get("risk_level") in {"medium", "high"} or spec.get("requires_confirmation"):
            args["dry_run"] = True
            args.pop("confirm", None)
            args.pop("confirmed", None)
        sanitized.append({"tool_name": name, "arguments": args})
    return sanitized
