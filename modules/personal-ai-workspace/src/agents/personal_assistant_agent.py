from __future__ import annotations

from typing import Any

from src.agents.llm_tool_planner import build_tool_plan, fallback_tool_plan
from src.generation.factory import build_llm_client
from src.observability.trace_logger import log_event
from src.tools.tool_registry import ToolRegistry


class PersonalAssistantAgent:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def run(self, goal: str) -> dict[str, Any]:
        config = self.registry.config
        if config.get("agent", {}).get("enable_tool_calling", True) and config.get("agent", {}).get("use_llm_planner", True):
            try:
                tool_plan = build_tool_plan(self.registry, goal)
            except Exception as exc:
                tool_plan = fallback_tool_plan(goal)
                tool_plan["planner_error"] = str(exc)
        else:
            tool_plan = fallback_tool_plan(goal)

        steps = []
        for call in tool_plan["tool_calls"]:
            result = self.registry.call(call["tool_name"], call.get("arguments", {}))
            steps.append({"tool_name": call["tool_name"], "arguments": call.get("arguments", {}), "result": result})

        output = {
            "success": all(step["result"].get("success", False) for step in steps),
            "goal": goal,
            "plan": tool_plan.get("plan", []),
            "planner_backend": tool_plan.get("planner_backend", ""),
            "steps": steps,
            "final_report": self._finalize(goal, tool_plan, steps),
        }
        log_event(config, "agent_runs.jsonl", output)
        return output

    def _finalize(self, goal: str, tool_plan: dict[str, Any], steps: list[dict[str, Any]]) -> str:
        reports = [step["result"].get("report", "") for step in steps if isinstance(step.get("result"), dict)]
        reports = [r for r in reports if r]
        if reports:
            return reports[-1]
        execution_status = self._execution_status(steps)
        prompt = (
            "Summarize these tool outputs into a concise final response. Tool outputs are authoritative. "
            "Do not claim facts that are not present in them. If an operation has executed=false or "
            "plan.dry_run=true, describe it as proposed and NOT executed; never call it saved, written, "
            "moved, renamed, or deleted.\n"
            f"Goal: {goal}\nHint: {tool_plan.get('final_response_hint', '')}"
        )
        try:
            summary = build_llm_client(self.registry.config).generate(prompt, [{"steps": steps}])
            return f"{execution_status}\n\n{summary}"
        except Exception:
            return f"{execution_status}\n\n" + "\n".join(str(step["result"])[:500] for step in steps)

    @staticmethod
    def _execution_status(steps: list[dict[str, Any]]) -> str:
        dry_run_count = 0
        executed_count = 0
        for step in steps:
            result = step.get("result") or {}
            plan = result.get("plan") if isinstance(result, dict) else None
            if result.get("executed") is False or isinstance(plan, dict) and plan.get("dry_run"):
                dry_run_count += 1
            elif result.get("executed") is True:
                executed_count += 1
        if dry_run_count:
            return (
                f"Execution status: {dry_run_count} write operation(s) were planned as dry runs and were not executed. "
                "Explicit user confirmation is required before any write occurs."
            )
        if executed_count:
            return f"Execution status: {executed_count} write operation(s) were executed after confirmation."
        return "Execution status: no write operation was executed."
