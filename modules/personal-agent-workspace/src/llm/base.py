from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: list[dict] | None = None) -> str:
        raise NotImplementedError

