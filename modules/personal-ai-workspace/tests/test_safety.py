import pytest

from src.config.config_loader import load_config
from src.safety.path_guard import PathGuard


def test_path_guard_blocks_traversal_and_env():
    guard = PathGuard(load_config())
    with pytest.raises(PermissionError):
        guard.resolve("../secret.txt")
    with pytest.raises(PermissionError):
        guard.resolve(".env")

