import sys
import types

from src.generation.openai_embedding import OpenAICompatibleEmbeddingClient
from src.generation.openai_llm import OpenAICompatibleLLMClient


class FakeChatCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "chat-model"
        assert kwargs["messages"][-1]["content"] == "hello"
        message = types.SimpleNamespace(content="world")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


class FakeEmbeddings:
    def create(self, **kwargs):
        assert kwargs["model"] == "embedding-model"
        data = [types.SimpleNamespace(embedding=[1.0, 0.0]) for _ in kwargs["input"]]
        return types.SimpleNamespace(data=data)


class FakeOpenAI:
    def __init__(self, api_key, base_url=None, timeout=60):
        assert api_key == "test-key"
        self.chat = types.SimpleNamespace(completions=FakeChatCompletions())
        self.embeddings = FakeEmbeddings()


def test_openai_compatible_llm_uses_sdk(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    client = OpenAICompatibleLLMClient(model_name="chat-model")
    assert client.generate("hello") == "world"


def test_openai_compatible_embedding_uses_sdk(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    client = OpenAICompatibleEmbeddingClient(model_name="embedding-model")
    assert client.embed_query("hello") == [1.0, 0.0]
    assert client.embed_texts(["a", "b"]) == [[1.0, 0.0], [1.0, 0.0]]
