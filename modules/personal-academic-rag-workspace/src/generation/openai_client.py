from __future__ import annotations

import os
from typing import Any

from src.generation.llm_client import BaseEmbeddingClient, BaseLLMClient


class OpenAICompatibleEmbeddingClient(BaseEmbeddingClient):
    """Embedding client for OpenAI and OpenAI-compatible APIs."""

    def __init__(
        self,
        model_name: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        timeout: float = 60,
        batch_size: int = 16,
        max_retries: int = 4,
    ) -> None:
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.timeout = timeout
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._client()
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = client.embeddings.create(model=self.model_name, input=batch)
            embeddings.extend(list(item.embedding) for item in response.data)
        return embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

    def _client(self) -> Any:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the openai package for embedding.backend=openai: pip install -r requirements.txt") from exc
        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)


class OpenAICompatibleLLMClient(BaseLLMClient):
    """Chat completion client for OpenAI and OpenAI-compatible APIs."""

    def __init__(
        self,
        model_name: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
        timeout: float = 60,
        max_retries: int = 4,
    ) -> None:
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

    def generate(self, prompt: str, context: list[dict] | None = None) -> str:
        context = context or []
        client = self._client()
        evidence = "\n\n".join(
            f"[{i}] {item.get('filename') or item.get('file_name') or 'unknown'} "
            f"page={item.get('page')} paragraph={item.get('paragraph')} chunk_id={item.get('chunk_id')}\n"
            f"{item.get('text', '')}"
            for i, item in enumerate(context, start=1)
        )
        system = (
            "You are a grounded academic RAG assistant. Answer only from the provided evidence. "
            "The caller invokes you only after evidence sufficiency has been verified. "
            "Give a concise answer in the question language, cite evidence with bracket numbers, "
            "and do not claim that evidence is insufficient when evidence chunks are provided."
        )
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{prompt}\n\nEvidence:\n{evidence}"},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""

    def _client(self) -> Any:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the openai package for llm.backend=openai: pip install -r requirements.txt") from exc
        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)
