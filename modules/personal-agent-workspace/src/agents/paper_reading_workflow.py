from __future__ import annotations

from src.agents.base_agent import BaseAgent


class PaperReadingWorkflow(BaseAgent):
    name = "PaperReadingWorkflow"

    def run(self, path: str, output: str) -> dict:
        return self.registry.call("read_papers", {"path": path, "output": output}).output

