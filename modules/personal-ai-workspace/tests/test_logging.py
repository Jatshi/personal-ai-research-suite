from src.config.config_loader import load_config
from src.observability.trace_logger import JsonlLogger
from src.tools.default_registry import build_registry


def test_tool_call_logging():
    config = load_config()
    build_registry(config).call("list_docs", {})
    assert JsonlLogger(config, "tool_calls.jsonl").tail(1)

