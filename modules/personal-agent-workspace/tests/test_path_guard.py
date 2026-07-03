from __future__ import annotations

import pytest

from src.config.config_loader import resolve_project_path
from src.safety.path_guard import PathGuard


def test_path_guard_blocks_traversal(cfg: dict) -> None:
    guard = PathGuard(resolve_project_path(cfg, cfg["app"]["workspace_dir"]))
    with pytest.raises(ValueError):
        guard.validate("../outside.txt")

