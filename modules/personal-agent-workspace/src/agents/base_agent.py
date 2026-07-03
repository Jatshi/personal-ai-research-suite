from __future__ import annotations

from src.tools.tool_registry import ToolRegistry
from src.workflows.state import AgentState


class BaseAgent:
    name = "BaseAgent"

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def new_state(self, goal: str) -> AgentState:
        return AgentState(goal=goal, agent_name=self.name)

