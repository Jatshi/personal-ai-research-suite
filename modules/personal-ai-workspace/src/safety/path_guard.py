from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config.config_loader import resolve_project_path


SENSITIVE_PATTERNS = (".env", ".pem", ".key", ".token", ".secret", "id_rsa", "id_ed25519", "credentials")


class PathGuard:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.workspace = resolve_project_path(config, config["app"]["workspace_dir"])
        self.workspace.mkdir(parents=True, exist_ok=True)

    def resolve(self, path: str | Path, *, must_exist: bool = False, for_write: bool = False) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.workspace / candidate
        resolved = candidate.resolve()
        if self.config["safety"].get("restrict_to_workspace", True):
            try:
                resolved.relative_to(self.workspace)
            except ValueError as exc:
                raise PermissionError(f"Path outside workspace blocked: {resolved}") from exc
        if self.config["safety"].get("block_hidden_files", True):
            for part in resolved.relative_to(self.workspace).parts:
                if part.startswith("."):
                    raise PermissionError(f"Hidden path blocked: {path}")
        if self.config["safety"].get("block_sensitive_files", True):
            lowered = resolved.name.lower()
            if lowered == ".env" or any(p in lowered for p in SENSITIVE_PATTERNS):
                raise PermissionError(f"Sensitive file blocked: {path}")
        if must_exist and not resolved.exists():
            raise FileNotFoundError(str(resolved))
        if for_write:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

