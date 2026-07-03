from __future__ import annotations

import time
from typing import Any, Callable

from src.safety.audit_log import JsonlLog
from src.tools.schemas import ToolSpec


class ToolRegistry:
    def __init__(self, tool_log: JsonlLog, security_log: JsonlLog) -> None:
        self.tool_log = tool_log
        self.security_log = security_log
        self._tools: dict[str, tuple[ToolSpec, Callable[..., dict[str, Any]]]] = {}

    def register(self, spec: ToolSpec, fn: Callable[..., dict[str, Any]]) -> None:
        self._tools[spec.name] = (spec, fn)

    def list_tools(self) -> list[dict[str, Any]]:
        return [{**spec.__dict__} for spec, _ in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        arguments = arguments or {}
        if name not in self._tools:
            return {"success": False, "error": f"Unknown tool: {name}"}
        spec, fn = self._tools[name]
        dry_run = bool(arguments.get("dry_run", spec.requires_confirmation))
        confirmed = bool(arguments.get("confirm", False))
        if spec.requires_confirmation and not dry_run and not confirmed:
            result = {"success": False, "error": "confirm=true required for non-dry-run operation", "requires_confirmation": True}
            self._log(spec, arguments, result, start, dry_run, confirmed)
            return result
        try:
            self._validate(spec, arguments)
            output = fn(**arguments)
            result = {"success": True, "data": output}
        except Exception as exc:
            result = {"success": False, "error": str(exc)}
            self.security_log.append({"tool_name": name, "error": str(exc), "risk_level": spec.risk_level, "arguments": self._sanitize(arguments)})
        self._log(spec, arguments, result, start, dry_run, confirmed)
        return result

    @staticmethod
    def _validate(spec: ToolSpec, arguments: dict[str, Any]) -> None:
        missing = [key for key in spec.input_schema.get("required", []) if key not in arguments]
        if missing:
            raise ValueError(f"Missing required arguments for {spec.name}: {missing}")

    @staticmethod
    def _sanitize(arguments: dict[str, Any]) -> dict[str, Any]:
        return {k: ("***" if "key" in k.lower() or "token" in k.lower() or "secret" in k.lower() else v) for k, v in arguments.items()}

    def _log(self, spec: ToolSpec, arguments: dict[str, Any], result: dict[str, Any], start: float, dry_run: bool, confirmed: bool) -> None:
        self.tool_log.append(
            {
                "tool_name": spec.name,
                "input_arguments": arguments,
                "sanitized_arguments": self._sanitize(arguments),
                "success": result.get("success", False),
                "error": result.get("error", ""),
                "affected_files": self._affected(arguments),
                "risk_level": spec.risk_level,
                "dry_run": dry_run,
                "confirmed": confirmed,
                "duration_ms": round((time.perf_counter() - start) * 1000, 3),
            }
        )

    @staticmethod
    def _affected(arguments: dict[str, Any]) -> list[str]:
        return [str(v) for k, v in arguments.items() if "path" in k and isinstance(v, str)]
