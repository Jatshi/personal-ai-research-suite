from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from src.config.config_loader import resolve_project_path


class JsonlLogger:
    def __init__(self, config: dict[str, Any], filename: str):
        log_dir = resolve_project_path(config, config["observability"]["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        self.path = log_dir / filename

    def write(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S"))
        event.setdefault("trace_id", uuid.uuid4().hex[:12])
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def tail(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        out: list[dict[str, Any]] = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"raw": line})
        return out


def log_event(config: dict[str, Any], filename: str, event: dict[str, Any]) -> None:
    JsonlLogger(config, filename).write(event)

