from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OperationPlan:
    operation: str
    source: str
    target: str | None = None
    risk_level: str = "low"
    dry_run: bool = True
    details: dict[str, Any] | None = None

