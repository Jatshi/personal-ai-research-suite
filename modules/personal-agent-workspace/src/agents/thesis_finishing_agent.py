from __future__ import annotations

from src.agents.base_agent import BaseAgent


class ThesisFinishingAgent(BaseAgent):
    name = "ThesisFinishingAgent"

    def check(self, path: str) -> dict:
        return self.registry.call("check_thesis", {"path": path}).output

