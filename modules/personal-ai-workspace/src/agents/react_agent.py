from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.generation.factory import build_llm_client
from src.memory.memory_store import MemoryStore
from src.observability.trace_logger import log_event
from src.tools.tool_registry import ToolRegistry


@dataclass
class ReActState:
    goal: str
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    termination_reason: str = ""


class ReActAgent:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.config = registry.config

    def run(self, goal: str, session_id: str = "default") -> dict[str, Any]:
        cfg = self.config.get("agent", {})
        memory = MemoryStore(self.config)
        memories = memory.search(session_id, goal, limit=5) if cfg.get("enable_long_term_memory", False) else []
        state = ReActState(goal=goal, session_id=session_id)
        state.messages = [{"role": "user", "content": self._initial_prompt(goal, memories)}]
        llm = build_llm_client(self.config)
        seen_actions: set[str] = set()
        repair_attempts: dict[str, int] = {}
        max_iterations = int(cfg.get("max_iterations", cfg.get("max_steps", 8)))

        for iteration in range(max_iterations):
            try:
                response = llm.complete_with_tools(state.messages, self.registry.openai_tools())
            except Exception as exc:
                return self._fallback_to_planner(goal, session_id, state, str(exc))
            if not response.tool_calls:
                state.termination_reason = "model_finished"
                final_answer = response.content or self._evidence_summary(state.steps)
                break
            call = response.tool_calls[0]
            fingerprint = f"{call.name}:{sorted(call.arguments.items())}"
            if fingerprint in seen_actions:
                state.termination_reason = "repeated_tool_call"
                final_answer = self._evidence_summary(state.steps)
                break
            seen_actions.add(fingerprint)
            result = self.registry.call(call.name, call.arguments)
            recovery: dict[str, Any] | None = None
            if not result.get("success", False) and call.name == "search_kb" and call.arguments.get("mode", "hybrid") != "keyword":
                fallback_args = {**call.arguments, "mode": "keyword"}
                fallback = self.registry.call(call.name, fallback_args)
                recovery = {"strategy": "hybrid_to_keyword", "result": fallback}
                result = fallback
            elif not result.get("success", False):
                repair_attempts[call.name] = repair_attempts.get(call.name, 0) + 1
                recovery = {"strategy": "llm_parameter_repair", "attempt": repair_attempts[call.name], "error": result.get("error", "")}
                if repair_attempts[call.name] > int(cfg.get("max_repair_attempts", 2)):
                    state.termination_reason = "tool_repair_exhausted"
                    final_answer = self._evidence_summary(state.steps)
                    break
            step = {"iteration": iteration + 1, "tool_name": call.name, "arguments": call.arguments, "result": result, "recovery": recovery}
            state.steps.append(step)
            if recovery:
                log_event(self.config, "agent_recovery.jsonl", {"goal": goal, "session_id": session_id, "tool_name": call.name, **recovery})
            # Preserve the OpenAI-compatible tool-message contract for the next
            # ReAct round. Some gateways reject the older flattened form.
            state.messages.append(
                {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": call.call_id,
                            "type": "function",
                            "function": {"name": call.name, "arguments": json.dumps(call.arguments, ensure_ascii=False)},
                        }
                    ],
                }
            )
            state.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.call_id,
                    "name": call.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str)[:12000],
                }
            )
        else:
            state.termination_reason = "max_iterations"
            final_answer = self._evidence_summary(state.steps)

        if cfg.get("enable_long_term_memory", False):
            memory.add(session_id, f"Goal: {goal}\nOutcome: {final_answer}", {"source": "react"}, importance=0.6)
        payload = {
            "success": bool(state.steps) or state.termination_reason == "model_finished",
            "goal": goal,
            "session_id": session_id,
            "mode": "react",
            "steps": state.steps,
            "termination_reason": state.termination_reason,
            "final_report": final_answer,
            "memory_count": len(memories),
        }
        log_event(self.config, "agent_runs.jsonl", payload)
        return payload

    def _fallback_to_planner(self, goal: str, session_id: str, state: ReActState, error: str) -> dict[str, Any]:
        """Degrade malformed provider tool-call payloads to the validated JSON planner."""
        from src.agents.llm_tool_planner import build_tool_plan, fallback_tool_plan

        try:
            plan = build_tool_plan(self.registry, goal)
        except Exception as exc:
            plan = fallback_tool_plan(goal)
            plan["planner_error"] = str(exc)
        steps = []
        for call in plan["tool_calls"]:
            steps.append({"tool_name": call["tool_name"], "arguments": call.get("arguments", {}), "result": self.registry.call(call["tool_name"], call.get("arguments", {}))})
        payload = {
            "success": all(step["result"].get("success", False) for step in steps),
            "goal": goal,
            "session_id": session_id,
            "mode": "react",
            "steps": steps,
            "termination_reason": "native_tool_call_provider_error",
            "fallback": {"strategy": "validated_json_planner", "error": error},
            "final_report": self._evidence_summary(steps),
            "memory_count": 0,
        }
        log_event(self.config, "agent_recovery.jsonl", {"goal": goal, "session_id": session_id, **payload["fallback"]})
        log_event(self.config, "agent_runs.jsonl", payload)
        return payload

    @staticmethod
    def _initial_prompt(goal: str, memories: list[dict[str, Any]]) -> str:
        context = "\n".join(f"- {item['content']}" for item in memories)
        return f"Complete this goal safely: {goal}\nRelevant durable memory:\n{context or '(none)'}"

    @staticmethod
    def _evidence_summary(steps: list[dict[str, Any]]) -> str:
        if not steps:
            return "No safe tool action was selected."
        return "Completed safe tool steps: " + ", ".join(step["tool_name"] for step in steps)
