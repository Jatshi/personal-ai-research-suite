from __future__ import annotations

import os
from typing import Any

from src.llm.base import BaseLLMClient


class OpenAICompatibleLLMClient(BaseLLMClient):
    def __init__(
        self,
        model_name: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        timeout: float = 60.0,
    ) -> None:
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("OpenAI backend requires `openai`. Install requirements.txt.") from exc
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {api_key_env}")
        kwargs: dict[str, Any] = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str, context: list[dict] | None = None) -> str:
        context = context or []
        context_text = "\n\n".join(
            f"[context {i + 1}]\n{item.get('text', '')}" for i, item in enumerate(context)
        )
        user_content = prompt if not context_text else f"{prompt}\n\nContext:\n{context_text}"
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a local personal AI agent. Use only provided local context when context is given. "
                        "Be concise, factual, and do not invent file contents."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""
