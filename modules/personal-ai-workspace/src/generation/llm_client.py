from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        raise NotImplementedError

