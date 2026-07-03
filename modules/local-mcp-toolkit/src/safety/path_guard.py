from __future__ import annotations

from pathlib import Path

from src.safety.sensitive_file_guard import SensitiveFileGuard


class PathGuard:
    def __init__(
        self,
        workspace_dir: str | Path,
        block_symlink_escape: bool = True,
        block_hidden_dirs: bool = True,
        block_sensitive_files: bool = True,
    ) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.block_symlink_escape = block_symlink_escape
        self.block_hidden_dirs = block_hidden_dirs
        self.sensitive_guard = SensitiveFileGuard() if block_sensitive_files else None

    def validate(self, path: str | Path, must_exist: bool = False, for_write: bool = False) -> Path:
        raw = Path(path)
        target = raw if raw.is_absolute() else self.workspace_dir / raw
        target = target.resolve()
        if self.workspace_dir != target and self.workspace_dir not in target.parents:
            raise PermissionError(f"Path outside workspace blocked: {target}")
        rel = target.relative_to(self.workspace_dir)
        if self.block_hidden_dirs and any(part.startswith(".") for part in rel.parts):
            raise PermissionError(f"Hidden path blocked: {target}")
        if self.sensitive_guard:
            self.sensitive_guard.validate(target)
        if must_exist and not target.exists():
            raise FileNotFoundError(str(target))
        if self.block_symlink_escape and target.exists() and target.is_symlink():
            resolved = target.resolve()
            if self.workspace_dir != resolved and self.workspace_dir not in resolved.parents:
                raise PermissionError(f"Symlink escapes workspace: {target}")
        if for_write:
            target.parent.mkdir(parents=True, exist_ok=True)
        return target

