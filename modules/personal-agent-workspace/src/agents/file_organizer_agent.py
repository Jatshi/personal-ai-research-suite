from __future__ import annotations

from src.agents.base_agent import BaseAgent


class FileOrganizerAgent(BaseAgent):
    name = "FileOrganizerAgent"

    def scan(self, path: str) -> dict:
        return self.registry.call("scan_folder", {"path": path}).output

    def organize(self, path: str) -> dict:
        return self.registry.call("organize_files", {"path": path}, dry_run=True).output

