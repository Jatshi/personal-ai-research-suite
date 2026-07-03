from __future__ import annotations

from pathlib import Path

import pytest

from src.config.config_loader import load_config, resolve_path
from src.safety.path_guard import PathGuard


def guard() -> PathGuard:
    cfg = load_config()
    return PathGuard(resolve_path(cfg, cfg["app"]["workspace_dir"]))


def test_path_traversal_blocked() -> None:
    g = guard()
    for bad in ["../secret.txt", "/etc/passwd", str(Path.cwd().parent)]:
        with pytest.raises(PermissionError):
            g.validate(bad)

