from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMToolResponse:
    content: str = ""
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    finish_reason: str = "stop"


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        raise NotImplementedError

    def complete_with_tools(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMToolResponse:
        """Return native tool calls when the provider supports them."""
        prompt = "\n".join(str(message.get("content", "")) for message in messages)
        return LLMToolResponse(content=self.generate(prompt), finish_reason="stop")
