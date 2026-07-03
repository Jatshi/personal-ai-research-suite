from src.agents.llm_tool_planner import _sanitize_calls, build_tool_plan
from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


def test_mock_llm_builds_tool_plan():
    registry = build_registry(load_config())
    plan = build_tool_plan(registry, "完成本周总结")
    assert plan["planner_backend"] == "mock"
    assert [c["tool_name"] for c in plan["tool_calls"]] == ["search_kb", "generate_weekly_report"]


def test_planner_sanitizes_high_risk_tools_to_dry_run():
    tools = [
        {"name": "write_note", "risk_level": "high", "requires_confirmation": True},
        {"name": "search_kb", "risk_level": "low", "requires_confirmation": False},
    ]
    calls = [
        {"tool_name": "write_note", "arguments": {"path": "notes/a.md", "content": "x", "dry_run": False, "confirm": True}},
        {"tool_name": "unknown", "arguments": {}},
    ]
    out = _sanitize_calls(calls, tools, max_steps=5)
    assert len(out) == 1
    assert out[0]["tool_name"] == "write_note"
    assert out[0]["arguments"]["dry_run"] is True
    assert "confirm" not in out[0]["arguments"]
