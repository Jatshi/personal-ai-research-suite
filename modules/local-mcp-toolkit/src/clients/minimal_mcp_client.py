from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.cli import _loads_args
from src.mcp_servers.combined_server import build_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool")
    parser.add_argument("--args", default="{}")
    parser.add_argument("--query")
    parser.add_argument("--repo-path")
    parser.add_argument("--list-tools", action="store_true")
    ns = parser.parse_args()
    registry = build_registry(load_config())
    if ns.list_tools or not ns.tool:
        print(json.dumps({"tools": registry.list_tools()}, ensure_ascii=False, indent=2))
        return
    args = _loads_args(ns.args)
    if ns.query:
        args.setdefault("query", ns.query)
        args.setdefault("question", ns.query)
    if ns.repo_path:
        args.setdefault("repo_path", ns.repo_path)
    print(json.dumps(registry.call(ns.tool, args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
