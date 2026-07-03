from __future__ import annotations

from typing import Any

from src.observability.trace_logger import log_event


def log_llm_call(config: dict[str, Any], prompt: str, response: str, backend: str = "mock", success: bool = True, error: str = "") -> None:
    log_event(
        config,
        "llm_calls.jsonl",
        {
            "prompt": prompt,
            "response": response,
            "model_backend": backend,
            "success": success,
            "error": error,
        },
    )
