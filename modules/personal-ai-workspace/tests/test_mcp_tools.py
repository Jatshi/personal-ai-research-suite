from __future__ import annotations

import asyncio

from src.config.config_loader import load_config
from src.mcp.mcp_server import build_fastmcp_server
from src.tools.default_registry import build_registry


def test_mcp_tool_schema_and_write_dry_run():
    registry = build_registry(load_config())
    specs = registry.list_tools()
    assert any(t["name"] == "write_note" and t["requires_confirmation"] for t in specs)
    result = registry.call("write_note", {"path": "notes/test.md", "content": "demo"})
    assert result["success"] and not result["executed"]


def test_fastmcp_registers_only_configured_tools_resources_and_prompts():
    server = build_fastmcp_server(load_config("config.production.yaml"))
    tool_names = {tool.name for tool in asyncio.run(server.list_tools())}
    resource_uris = {str(resource.uri) for resource in asyncio.run(server.list_resources())}
    template_uris = {str(template.uriTemplate) for template in asyncio.run(server.list_resource_templates())}
    prompt_names = {prompt.name for prompt in asyncio.run(server.list_prompts())}

    assert tool_names == {"search_kb", "ask_kb", "list_docs", "summarize_doc", "write_note", "generate_weekly_report"}
    assert resource_uris == {"scholarmind://collections", "scholarmind://logs/recent"}
    assert template_uris == {"scholarmind://documents/{collection}", "scholarmind://document/{doc_id}"}
    assert prompt_names == {"grounded-rag-answer", "research-summary", "safe-note-writing"}
