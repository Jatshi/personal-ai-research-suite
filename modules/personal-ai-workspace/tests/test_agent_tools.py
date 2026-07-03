from src.config.config_loader import load_config
from src.tools.default_registry import build_registry


def test_registry_has_core_tools():
    tools = {t["name"] for t in build_registry(load_config()).list_tools()}
    assert {"search_kb", "ask_kb", "write_note", "generate_weekly_report"} <= tools


def test_personal_assistant_agent_uses_llm_planner():
    from src.agents.personal_assistant_agent import PersonalAssistantAgent

    result = PersonalAssistantAgent(build_registry(load_config())).run("完成本周总结")
    assert result["success"]
    assert result["planner_backend"] == "mock"
    assert [s["tool_name"] for s in result["steps"]] == ["search_kb", "generate_weekly_report"]
