from __future__ import annotations

from typing import Any

from src.llm.base import BaseLLMClient
from src.llm.mock_llm import MockLLMClient
from src.llm.openai_client import OpenAICompatibleLLMClient


def build_llm_client(config: dict[str, Any]) -> BaseLLMClient:
    llm_config = config.get("llm", {})
    backend = str(llm_config.get("backend", "mock")).lower()
    if backend == "mock" or config.get("app", {}).get("mock_mode", False):
        return MockLLMClient()
    if backend in {"openai", "openai-compatible", "ollama"}:
        return OpenAICompatibleLLMClient(
            model_name=str(llm_config.get("model_name", "gpt-4o-mini")),
            api_key_env=str(llm_config.get("api_key_env", "OPENAI_API_KEY")),
            base_url=llm_config.get("base_url"),
            temperature=float(llm_config.get("temperature", 0.2)),
            max_tokens=int(llm_config.get("max_tokens", 1200)),
            timeout=float(llm_config.get("timeout", 60)),
        )
    raise ValueError(f"Unsupported llm backend: {backend}")
