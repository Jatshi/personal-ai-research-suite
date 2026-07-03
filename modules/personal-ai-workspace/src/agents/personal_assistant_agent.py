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
        prompt = (
            "Summarize these tool outputs into a concise final response. "
            "Do not claim facts that are not present in the tool outputs.\n"
            f"Goal: {goal}\nHint: {tool_plan.get('final_response_hint', '')}"
        )
        try:
            return build_llm_client(self.registry.config).generate(prompt, [{"steps": steps}])
        except Exception:
            return "\n".join(str(step["result"])[:500] for step in steps)
