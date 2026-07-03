from __future__ import annotations

from src.config.config_loader import load_config
from src.mcp_servers.combined_server import build_registry


def test_tool_registry_lists_categories() -> None:
    tools = build_registry(load_config()).list_tools()
    categories = {tool["category"] for tool in tools}
    assert {"rag", "filesystem", "code"} <= categories

