from __future__ import annotations

import fnmatch
from pathlib import Path


SENSITIVE_PATTERNS = [
    ".env",
    "*.env",
    "*.key",
    "*.pem",
    "*.crt",
    "*.p12",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.*",
    "*.secret",
    "*.token",
]


class SensitiveFileGuard:
    def __init__(self, patterns: list[str] | None = None) -> None:
        self.patterns = patterns or SENSITIVE_PATTERNS

    def validate(self, path: str | Path) -> None:
        name = Path(path).name
        for pattern in self.patterns:
            if fnmatch.fnmatch(name, pattern):
                raise PermissionError(f"Sensitive file access blocked: {name}")
