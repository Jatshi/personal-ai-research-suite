import pytest

from src.generation.factory import build_embedding_client, build_llm_client
from src.generation.mock_embedding import MockEmbeddingClient
from src.generation.mock_llm import MockLLMClient


def test_factory_uses_mock_by_default():
    config = {"llm": {"backend": "mock"}, "embedding": {"backend": "mock", "dimension": 16}}
    assert isinstance(build_llm_client(config), MockLLMClient)
    assert isinstance(build_embedding_client(config), MockEmbeddingClient)


def test_openai_backend_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = {
        "llm": {"backend": "openai", "model_name": "gpt-4.1-mini", "api_key_env": "OPENAI_API_KEY"},
        "embedding": {"backend": "openai", "model_name": "text-embedding-3-small", "api_key_env": "OPENAI_API_KEY"},
    }
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_llm_client(config)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_embedding_client(config)
