from __future__ import annotations

from typing import Any

from src.observability.trace_logger import log_event


def log_error(config: dict[str, Any], message: str, where: str = "") -> None:
    log_event(config, "errors.jsonl", {"message": message, "where": where, "success": False})

