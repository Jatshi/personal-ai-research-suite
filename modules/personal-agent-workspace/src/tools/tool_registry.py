from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable

from src.safety.audit_log import JsonlAuditLog


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    risk_level: str
    requires_confirmation: bool


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: str = ""
    dry_run: bool = False
    requires_confirmation: bool = False


class ToolRegistry:
    def __init__(self, tool_log: JsonlAuditLog) -> None:
        self.tool_log = tool_log
        self._tools: dict[str, tuple[ToolSpec, Callable[..., Any]]] = {}

    def register(self, spec: ToolSpec, fn: Callable[..., Any]) -> None:
        self._tools[spec.name] = (spec, fn)

    def specs(self) -> list[ToolSpec]:
        return [spec for spec, _ in self._tools.values()]

    def call(self, name: str, params: dict[str, Any] | None = None, confirmed: bool = False, dry_run: bool | None = None) -> ToolResult:
        params = params or {}
        if name not in self._tools:
            return ToolResult(False, error=f"Unknown tool: {name}")
        spec, fn = self._tools[name]
        effective_dry_run = spec.risk_level in {"medium", "high"} if dry_run is None else dry_run
        if spec.requires_confirmation and not confirmed and not effective_dry_run:
            result = ToolResult(False, error="Confirmation required", dry_run=effective_dry_run, requires_confirmation=True)
            self._log(name, params, result)
            return result
        try:
            self._validate_params(spec, params)
            sig = inspect.signature(fn)
            if "dry_run" in sig.parameters:
                params = {**params, "dry_run": effective_dry_run}
            if "confirmed" in sig.parameters:
                params = {**params, "confirmed": confirmed}
            output = fn(**params)
            result = ToolResult(True, output=output, dry_run=effective_dry_run, requires_confirmation=spec.requires_confirmation)
        except Exception as exc:
            result = ToolResult(False, error=str(exc), dry_run=effective_dry_run, requires_confirmation=spec.requires_confirmation)
        self._log(name, params, result)
        return result

    @staticmethod
    def _validate_params(spec: ToolSpec, params: dict[str, Any]) -> None:
        required = spec.input_schema.get("required", [])
        missing = [key for key in required if key not in params]
        if missing:
            raise ValueError(f"Missing required params for {spec.name}: {missing}")
        properties = spec.input_schema.get("properties", {})
        if properties:
            unknown = sorted(set(params) - set(properties))
            if unknown:
                raise ValueError(f"Unknown params for {spec.name}: {unknown}")
            for key, schema in properties.items():
                if key not in params:
                    continue
                expected = schema.get("type")
                if expected and not _matches_json_type(params[key], expected):
                    raise TypeError(f"Param {key} for {spec.name} must be {expected}")

    def _log(self, name: str, params: dict[str, Any], result: ToolResult) -> None:
        spec = self._tools[name][0] if name in self._tools else None
        self.tool_log.write(
            {
                "tool_name": name,
                "risk_level": spec.risk_level if spec else "unknown",
                "input": params,
                "output": result.output,
                "success": result.success,
                "error": result.error,
                "dry_run": result.dry_run,
                "requires_confirmation": result.requires_confirmation,
            }
        )


def _matches_json_type(value: Any, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    for item in expected_types:
        py_type = mapping.get(item)
        if py_type is None:
            continue
        if item == "integer" and isinstance(value, bool):
            continue
        if isinstance(value, py_type):
            return True
    return False
