from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from src.observability.trace_logger import log_event


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    risk_level: str = "low"
    requires_confirmation: bool = False
    category: str = "general"


ToolFunc = Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._tools: dict[str, tuple[ToolSpec, ToolFunc]] = {}

    def register(self, spec: ToolSpec, func: ToolFunc) -> None:
        self._tools[spec.name] = (spec, func)

    def list_tools(self) -> list[dict[str, Any]]:
        return [{**spec.__dict__} for spec, _ in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name not in self._tools:
            return {"success": False, "error": f"Unknown tool: {name}"}
        spec, func = self._tools[name]
        started = time.time()
        dry_run = bool(arguments.get("dry_run", spec.risk_level in {"medium", "high"}))
        confirmed = bool(arguments.get("confirm") or arguments.get("confirmed"))
        if spec.requires_confirmation and not dry_run and not confirmed:
            result = {"success": False, "error": f"Tool {name} requires confirmation", "requires_confirmation": True}
        else:
            try:
                payload = dict(arguments)
                payload["dry_run"] = dry_run
                payload["confirmed"] = confirmed
                result = func(payload)
            except Exception as exc:
                result = {"success": False, "error": str(exc)}
        latency_ms = int((time.time() - started) * 1000)
        log_event(
            self.config,
            "tool_calls.jsonl",
            {
                "tool_name": name,
                "input": arguments,
                "output": result,
                "risk_level": spec.risk_level,
                "dry_run": dry_run,
                "confirmed": confirmed,
                "latency_ms": latency_ms,
                "success": result.get("success", False),
            },
        )
        return result

