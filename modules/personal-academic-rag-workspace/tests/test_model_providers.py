from __future__ import annotations

import sys
import types

import pytest

from src.config.config_loader import load_config
from src.generation.mock_llm import MockEmbeddingClient, MockLLMClient
from src.generation.openai_client import OpenAICompatibleEmbeddingClient, OpenAICompatibleLLMClient
from src.generation.providers import build_embedding_client, build_llm_client


def test_provider_factory_defaults_to_mock():
    config = {
        "embedding": {"backend": "mock", "dimension": 64},
        "llm": {"backend": "mock"},
    }
    assert isinstance(build_embedding_client(config), MockEmbeddingClient)
    assert isinstance(build_llm_client(config), MockLLMClient)


def test_openai_client_requires_env_var(monkeypatch):
    monkeypatch.delenv("MISSING_TEST_KEY", raising=False)
    client = OpenAICompatibleLLMClient(model_name="gpt-test", api_key_env="MISSING_TEST_KEY")
    with pytest.raises(RuntimeError, match="Missing API key"):
        client.generate("hello", [])


def test_load_config_uses_env_override(monkeypatch):
    monkeypatch.setenv("PERSONAL_ACADEMIC_RAG_CONFIG", "config.production.yaml")
    config = load_config()
    assert config["llm"]["backend"] == "openai"
    assert config["embedding"]["backend"] == "openai"


def test_openai_compatible_clients_call_sdk(monkeypatch):
    class FakeEmbeddings:
        def create(self, **kwargs):
            assert kwargs["model"] == "embedding-test"
            assert kwargs["input"] == ["hello"]
            return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[1.0, 0.0])])

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["model"] == "chat-test"
            assert kwargs["messages"][0]["role"] == "system"
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="OK"))])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "test-key"

        embeddings = FakeEmbeddings()
        chat = types.SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))

    assert OpenAICompatibleEmbeddingClient("embedding-test").embed_query("hello") == [1.0, 0.0]
    assert OpenAICompatibleLLMClient("chat-test").generate("Say OK", [{"text": "evidence"}]) == "OK"
