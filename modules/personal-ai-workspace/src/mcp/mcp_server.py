from __future__ import annotations

import json
import sys
from typing import Any

from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


def serve_stdio(config: dict[str, Any] | None = None) -> None:
    config = config or load_config()
    registry = build_registry(config)
    print(json.dumps({"server": config["mcp"]["server_name"], "mode": "mcp-like-json-stdio"}), flush=True)
    for line in sys.stdin:
        try:
            req = json.loads(line)
            method = req.get("method")
            if method == "tools/list":
                resp = {"success": True, "tools": registry.list_tools()}
            elif method == "tools/call":
                resp = registry.call(req["tool"], req.get("arguments", {}))
            else:
                resp = {"success": False, "error": f"Unknown method: {method}"}
        except Exception as exc:
            resp = {"success": False, "error": str(exc)}
        print(json.dumps(resp, ensure_ascii=False), flush=True)

