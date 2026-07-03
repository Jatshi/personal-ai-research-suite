from __future__ import annotations

import hashlib
import math
from collections import Counter

from src.generation.llm_client import BaseEmbeddingClient, BaseLLMClient
from src.utils.text_utils import normalize_text, tokenize


INSUFFICIENT_EVIDENCE_MESSAGE = "知识库中没有足够证据回答该问题。"


class MockEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed(query)

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        counts = Counter(tokenize(text))
        for token, count in counts.items():
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[idx] += float(count)
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec


class MockLLMClient(BaseLLMClient):
    def generate(self, prompt: str, context: list[dict] | None = None) -> str:
        context = context or []
        if not context:
            return INSUFFICIENT_EVIDENCE_MESSAGE

        bullets = []
        for i, item in enumerate(context[:4], start=1):
            text = normalize_text(item.get("text", ""))[:260]
            filename = item.get("filename") or item.get("file_name") or "unknown"
            chunk_id = item.get("chunk_id", "")
            if text:
                bullets.append(f"{i}. {text} 来源：{filename}, chunk_id={chunk_id}")

        if not bullets:
            return INSUFFICIENT_EVIDENCE_MESSAGE
        return "Mock answer: 以下回答只基于检索到的证据片段生成。\n\n" + "\n".join(bullets)
