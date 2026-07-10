from __future__ import annotations

import os
from typing import Any

from src.generation.llm_client import BaseEmbeddingClient, BaseLLMClient
from src.generation.mock_llm import MockEmbeddingClient, MockLLMClient
from src.generation.openai_client import OpenAICompatibleEmbeddingClient, OpenAICompatibleLLMClient


def build_embedding_client(config: dict[str, Any]) -> BaseEmbeddingClient:
    embedding_config = config.get("embedding", {})
    backend = str(embedding_config.get("backend", "mock")).lower()
    if backend in {"mock", "local_mock"}:
        return MockEmbeddingClient(int(embedding_config.get("dimension", 384)))
    if backend in {"openai", "openai_compatible"}:
        return OpenAICompatibleEmbeddingClient(
            model_name=embedding_config.get("model_name", "text-embedding-3-small"),
            api_key_env=embedding_config.get("api_key_env", "OPENAI_API_KEY"),
            base_url=embedding_config.get("base_url") or os.getenv("OPENAI_BASE_URL"),
            timeout=float(embedding_config.get("timeout", 60)),
            batch_size=int(embedding_config.get("batch_size", 16)),
            max_retries=int(embedding_config.get("max_retries", 4)),
        )
    raise ValueError(f"Unsupported embedding backend: {backend}")


def build_llm_client(config: dict[str, Any]) -> BaseLLMClient:
    llm_config = config.get("llm", {})
    backend = str(llm_config.get("backend", "mock")).lower()
    if backend in {"mock", "local_mock"}:
        return MockLLMClient()
    if backend in {"openai", "openai_compatible"}:
        return OpenAICompatibleLLMClient(
            model_name=llm_config.get("model_name", "gpt-4o-mini"),
            api_key_env=llm_config.get("api_key_env", "OPENAI_API_KEY"),
            base_url=llm_config.get("base_url") or os.getenv("OPENAI_BASE_URL"),
            temperature=float(llm_config.get("temperature", 0.2)),
            max_tokens=int(llm_config.get("max_tokens", 1000)),
            timeout=float(llm_config.get("timeout", 60)),
            max_retries=int(llm_config.get("max_retries", 4)),
        )
    raise ValueError(f"Unsupported LLM backend: {backend}")
