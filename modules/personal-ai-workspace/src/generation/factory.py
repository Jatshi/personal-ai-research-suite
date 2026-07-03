from __future__ import annotations

from typing import Any

from src.generation.embedding_client import BaseEmbeddingClient
from src.generation.llm_client import BaseLLMClient
from src.generation.mock_embedding import MockEmbeddingClient
from src.generation.mock_llm import MockLLMClient
from src.generation.openai_embedding import OpenAICompatibleEmbeddingClient
from src.generation.openai_llm import OpenAICompatibleLLMClient


OPENAI_BACKENDS = {"openai", "openai_compatible", "compatible"}


def build_llm_client(config: dict[str, Any]) -> BaseLLMClient:
    llm_cfg = config.get("llm", {})
    backend = str(llm_cfg.get("backend", "mock")).lower()
    if backend == "mock":
        return MockLLMClient()
    if backend in OPENAI_BACKENDS:
        return OpenAICompatibleLLMClient(
            model_name=llm_cfg.get("model_name", "gpt-4.1-mini"),
            api_key_env=llm_cfg.get("api_key_env", "OPENAI_API_KEY"),
            base_url_env=llm_cfg.get("base_url_env", "OPENAI_BASE_URL"),
            temperature=float(llm_cfg.get("temperature", 0.2)),
            max_tokens=int(llm_cfg.get("max_tokens", 1200)),
            timeout_seconds=int(llm_cfg.get("timeout_seconds", 60)),
            system_prompt=llm_cfg.get("system_prompt", ""),
        )
    raise ValueError(f"Unsupported llm.backend: {backend}")


def build_embedding_client(config: dict[str, Any]) -> BaseEmbeddingClient:
    emb_cfg = config.get("embedding", {})
    backend = str(emb_cfg.get("backend", "mock")).lower()
    if backend == "mock":
        return MockEmbeddingClient(int(emb_cfg.get("dimension", 384)))
    if backend in OPENAI_BACKENDS:
        return OpenAICompatibleEmbeddingClient(
            model_name=emb_cfg.get("model_name", "text-embedding-3-small"),
            api_key_env=emb_cfg.get("api_key_env", "OPENAI_API_KEY"),
            base_url_env=emb_cfg.get("base_url_env", "OPENAI_BASE_URL"),
            timeout_seconds=int(emb_cfg.get("timeout_seconds", 60)),
        )
    raise ValueError(f"Unsupported embedding.backend: {backend}")
