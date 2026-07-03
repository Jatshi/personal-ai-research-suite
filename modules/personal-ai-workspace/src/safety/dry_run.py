from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class OperationPlan:
    operation: str
    target: str
    dry_run: bool = True
    confirmed: bool = False
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

