from __future__ import annotations

import importlib.util

import pytest

from src.config.config_loader import load_config
from src.evaluation.ragas_evaluator import eval_ragas
from src.generation.mock_embedding import MockEmbeddingClient
from src.generation.mock_llm import MockLLMClient


@pytest.mark.skipif(importlib.util.find_spec("lightrag") is None, reason="production LightRAG extra is not installed")
def test_lightrag_adapter_accepts_workspace_clients(tmp_path):
    from src.graphrag.lightrag_adapter import LightRAGAdapter

    adapter = LightRAGAdapter(str(tmp_path / "lightrag"), MockLLMClient(), MockEmbeddingClient(384), 384, "mock-embedding")
    assert adapter.rag is not None


@pytest.mark.skipif(importlib.util.find_spec("ragas") is None or importlib.util.find_spec("langchain_openai") is None, reason="production RAGAS extra is not installed")
def test_ragas_evaluator_requires_explicit_api_key(monkeypatch, tmp_path):
    config = load_config()
    config["llm"]["api_key_env"] = "SCHOLARMIND_RAGAS_TEST_KEY"
    monkeypatch.delenv("SCHOLARMIND_RAGAS_TEST_KEY", raising=False)
    dataset = tmp_path / "eval.jsonl"
    dataset.write_text('{"question":"RAG"}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="Missing evaluator API key"):
        eval_ragas(config, str(dataset))
