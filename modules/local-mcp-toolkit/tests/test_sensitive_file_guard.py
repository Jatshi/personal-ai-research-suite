from __future__ import annotations

import pytest

from src.config.config_loader import load_config, resolve_path
from src.safety.path_guard import PathGuard


def test_sensitive_files_blocked() -> None:
    cfg = load_config()
    g = PathGuard(resolve_path(cfg, cfg["app"]["workspace_dir"]))
    for name in ["docs/fake.env", "docs/fake_key.pem"]:
        with pytest.raises(PermissionError):
            g.validate(name, must_exist=True)
    with pytest.raises(PermissionError):
        g.validate(".hidden/file.txt")

