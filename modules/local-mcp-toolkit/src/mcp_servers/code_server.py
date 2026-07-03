from __future__ import annotations

from src.config.config_loader import load_config
from src.mcp_servers.combined_server import build_registry, run_stdio_server


def main() -> None:
    run_stdio_server(build_registry(load_config(), ["code"]))


if __name__ == "__main__":
    main()

