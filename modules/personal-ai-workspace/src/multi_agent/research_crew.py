from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.generation.factory import build_llm_client
from src.multi_agent.crew import AgentRole, Crew, Task
from src.observability.trace_logger import log_event
from src.tools.kb_tools import search_kb_tool


def run_research_crew(config: dict[str, Any], topic: str, collection: str | None = None, top_k: int = 8) -> dict[str, Any]:
    evidence = search_kb_tool(config, {"query": topic, "collection": collection, "top_k": top_k}).get("results", [])
    roles = _research_roles(config)
    tasks = [
        Task("reader", f"Extract the research question, paper metadata, and key claims for: {topic}", roles["reader"], "Structured reading summary"),
        Task("method", "Analyze the method, assumptions, components, and stated novelty.", roles["method"], "Method analysis"),
        Task("experiment", "Extract datasets, metrics, baselines, and observed results.", roles["experiment"], "Experiment analysis"),
        Task("critic", "Identify limitations, reproducibility risks, and evidence gaps.", roles["critic"], "Critical assessment"),
        Task("writer", "Synthesize prior outputs into a concise evidence-grounded research note with source names.", roles["writer"], "Final research note"),
    ]
    def role_llm(role: AgentRole):
        """Create a role-specific client only when its config overrides are enabled."""
        if not role.llm_overrides:
            return shared_llm
        role_config = deepcopy(config)
        role_config.setdefault("llm", {}).update(role.llm_overrides)
        return build_llm_client(role_config)

    shared_llm = build_llm_client(config)
    state = Crew(tasks, role_llm).run({"topic": topic, "collection": collection, "evidence": evidence})
    result = {
        "success": True,
        "topic": topic,
        "collection": collection,
        "evidence_count": len(evidence),
        "outputs": state["outputs"],
        "steps": state["steps"],
        "final_note": state["outputs"].get("writer", ""),
    }
    log_event(config, "multi_agent_runs.jsonl", result)
    return result


def _research_roles(config: dict[str, Any] | None = None) -> dict[str, AgentRole]:
    configured_roles = (config or {}).get("multi_agent", {}).get("roles", {})
    def overrides(name: str) -> dict[str, Any]:
        return dict(configured_roles.get(name, {}).get("llm", {}))
    return {
        "reader": AgentRole("Reader", "Extract paper facts", "Identify only facts present in the evidence.", ["search_kb"], overrides("reader")),
        "method": AgentRole("Method", "Analyze technical method", "Explain method components and do not infer missing details.", ["search_kb"], overrides("method")),
        "experiment": AgentRole("Experiment", "Analyze evaluation", "Extract datasets, metrics and results only when cited.", ["search_kb"], overrides("experiment")),
        "critic": AgentRole("Critic", "Assess limitations", "Separate explicit limitations from cautious inferences.", ["search_kb"], overrides("critic")),
        "writer": AgentRole("Writer", "Synthesize research note", "Integrate shared outputs and identify evidence gaps.", ["search_kb"], overrides("writer")),
    }
