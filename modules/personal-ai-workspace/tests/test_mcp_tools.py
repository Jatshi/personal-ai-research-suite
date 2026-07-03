from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


def test_mcp_tool_schema_and_write_dry_run():
    registry = build_registry(load_config())
    specs = registry.list_tools()
    assert any(t["name"] == "write_note" and t["requires_confirmation"] for t in specs)
    result = registry.call("write_note", {"path": "notes/test.md", "content": "demo"})
    assert result["success"] and not result["executed"]

