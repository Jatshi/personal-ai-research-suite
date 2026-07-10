from __future__ import annotations

import asyncio

from src.config.config_loader import load_config
from src.mcp_servers.combined_server import build_fastmcp_server, build_registry


def test_fastmcp_exposes_tools_resources_and_prompts() -> None:
    server = build_fastmcp_server(build_registry(load_config()))
    tools = asyncio.run(server.list_tools())
    resources = asyncio.run(server.list_resources())
    prompts = asyncio.run(server.list_prompts())
    assert any(tool.name == "search_documents" for tool in tools)
    assert any(str(resource.uri) == "scholarmind://collections" for resource in resources)
    assert any(prompt.name == "grounded_rag_answer" for prompt in prompts)
