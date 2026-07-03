from __future__ import annotations

from pathlib import Path

from src.utils.file_utils import is_hidden

SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials.json",
    "token.json",
}


class PathGuard:
    def __init__(self, workspace_dir: str | Path, block_hidden: bool = True, block_env: bool = True, allow_outside: bool = False) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()
        self.block_hidden = block_hidden
        self.block_env = block_env
        self.allow_outside = allow_outside
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, path: str | Path, must_exist: bool = False, for_write: bool = False) -> Path:
        target = Path(path)
        if not target.is_absolute():
            target = self.workspace_dir / target
        target = target.resolve()
        if not self.allow_outside and self.workspace_dir != target and self.workspace_dir not in target.parents:
            raise ValueError(f"Path outside workspace is blocked: {target}")
        relative = target.relative_to(self.workspace_dir) if self.workspace_dir in target.parents or target == self.workspace_dir else target
        if self.block_hidden and is_hidden(relative):
            raise ValueError(f"Hidden files or directories are blocked: {target}")
        if self.block_env and target.name.lower() in SECRET_FILE_NAMES:
            raise ValueError(f"Secret-like file is blocked: {target.name}")
        if must_exist and not target.exists():
            raise FileNotFoundError(str(target))
        if for_write:
            target.parent.mkdir(parents=True, exist_ok=True)
        return target
