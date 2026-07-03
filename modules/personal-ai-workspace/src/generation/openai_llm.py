from __future__ import annotations

import os
from typing import Any

from src.generation.llm_client import BaseLLMClient


class OpenAICompatibleLLMClient(BaseLLMClient):
    """Chat-completions client for OpenAI and OpenAI-compatible gateways."""

    def __init__(
        self,
        model_name: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url_env: str = "OPENAI_BASE_URL",
        temperature: float = 0.2,
        max_tokens: int = 1200,
        timeout_seconds: int = 60,
        system_prompt: str = "",
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional install state
            raise RuntimeError("openai package is required for llm.backend=openai") from exc

        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {api_key_env}")
        base_url = os.getenv(base_url_env) or None
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or "Answer accurately using the supplied context."

    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        messages: list[dict[str, str]] = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({"role": "user", "content": _format_context(context)})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""


def _format_context(context: list[dict[str, Any]]) -> str:
    parts = ["Evidence chunks:"]
    for idx, item in enumerate(context, 1):
        source = item.get("file_name") or item.get("title") or "unknown"
        location = item.get("page_number") or item.get("paragraph_number") or item.get("chunk_id", "")
        text = item.get("text") or item.get("snippet") or ""
        parts.append(f"[{idx}] source={source}, location={location}, chunk_id={item.get('chunk_id','')}\n{text}")
    return "\n\n".join(parts)
