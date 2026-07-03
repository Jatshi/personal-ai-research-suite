from __future__ import annotations

from pathlib import Path

from src.utils.file_utils import copy_into_workspace, ensure_within


class FileRegistry:
    def __init__(self, project_root: Path, raw_dir: Path) -> None:
        self.project_root = project_root.resolve()
        self.raw_dir = ensure_within(self.project_root, raw_dir)

    def register(self, source: Path, collection: str) -> Path:
        return copy_into_workspace(source.resolve(), self.raw_dir, collection)
