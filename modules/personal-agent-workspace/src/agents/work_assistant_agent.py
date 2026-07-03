from __future__ import annotations

from src.agents.base_agent import BaseAgent


class WorkAssistantAgent(BaseAgent):
    name = "WorkAssistantAgent"

    def assistant(self, goal: str) -> str:
        return self.registry.call("generate_todo_list", {"goal": goal}).output

    def daily_report(self, todo: str) -> str:
        return self.registry.call("generate_daily_report", {"todo_path": todo}).output

    def weekly_report(self, todo: str) -> str:
        return self.registry.call("generate_weekly_report", {"todo_path": todo}).output

