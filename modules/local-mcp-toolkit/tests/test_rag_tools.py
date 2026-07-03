from __future__ import annotations

from src.config.config_loader import load_config
from src.mcp_servers.combined_server import build_registry


def test_search_documents_structured() -> None:
    registry = build_registry(load_config(), ["rag"])
    res = registry.call("search_documents", {"query": "RAG evidence", "top_k": 3})
    assert res["success"]
    assert "results" in res["data"]
    assert res["data"]["results"]


def test_ask_insufficient_evidence() -> None:
    registry = build_registry(load_config(), ["rag"])
    res = registry.call("ask_knowledge_base", {"question": "火星殖民地预算是多少"})
    assert res["success"]
    assert not res["data"]["evidence_sufficient"]
    assert res["data"]["answer"] == "知识库中没有足够证据回答该问题。"

