from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    goal: str
    agent_name: str
    intermediate_results: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    approvals: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    final_report: str = ""

    def record(self, key: str, value: Any) -> None:
        self.intermediate_results[key] = value

