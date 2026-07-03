from __future__ import annotations

from typing import Any

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


def call_tool(tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_registry(load_config()).call(tool, args or {})

