from __future__ import annotations

from typing import Any

from src.agents.react_agent import ReActAgent
from src.generation.llm_client import BaseLLMClient, LLMToolCall, LLMToolResponse
from src.memory.memory_store import MemoryStore
from src.config.config_loader import load_config
from src.tools.default_registry import build_registry
from src.tools.tool_registry import ToolSpec


class ScriptedLLM(BaseLLMClient):
    def __init__(self) -> None:
        self.calls = 0
        self.messages: list[list[dict[str, Any]]] = []

    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        return "done"

    def complete_with_tools(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMToolResponse:
        self.calls += 1
        self.messages.append(messages)
        if self.calls == 1:
            return LLMToolResponse(tool_calls=[LLMToolCall("1", "list_files", {"path": "."})], finish_reason="tool_calls")
        return LLMToolResponse(content="safe completion")


class BrokenToolLLM(BaseLLMClient):
    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        return ""

    def complete_with_tools(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMToolResponse:
        raise RuntimeError("provider returned malformed tool call")


def test_tool_spec_exports_openai_schema():
    tool = ToolSpec("search", "Search", {"query": "str"})
    exported = tool.to_openai_tool()
    assert exported["function"]["parameters"]["properties"]["query"]["type"] == "string"


def test_react_uses_native_tool_response(monkeypatch, tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    config["app"]["workspace_dir"] = "./examples/sample_workspace"
    registry = build_registry(config)
    llm = ScriptedLLM()
    monkeypatch.setattr("src.agents.react_agent.build_llm_client", lambda config: llm)
    result = ReActAgent(registry).run("inspect files", "test-session")
    assert result["termination_reason"] == "model_finished"
    assert result["steps"][0]["tool_name"] == "list_files"
    tool_call = llm.messages[1][-2]["tool_calls"][0]
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "list_files"
    assert llm.messages[1][-1]["tool_call_id"] == "1"


def test_memory_filters_secrets(tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    store = MemoryStore(config)
    assert store.add("scope", "OPENAI_API_KEY=sk-secret") is None
    assert store.add("scope", "User prefers concise research summaries") is not None


def test_react_degrades_when_provider_tool_calls_are_malformed(monkeypatch, tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    registry = build_registry(config)
    monkeypatch.setattr("src.agents.react_agent.build_llm_client", lambda config: BrokenToolLLM())
    result = ReActAgent(registry).run("safe fallback")
    assert result["termination_reason"] == "native_tool_call_provider_error"
    assert result["fallback"]["strategy"] == "validated_json_planner"
