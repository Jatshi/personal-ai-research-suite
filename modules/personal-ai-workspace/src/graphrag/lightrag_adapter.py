from __future__ import annotations

from typing import Any

from src.generation.embedding_client import BaseEmbeddingClient
from src.generation.llm_client import BaseLLMClient


class LightRAGAdapter:
    """Optional LightRAG bridge using the workspace's OpenAI-compatible clients."""

    def __init__(self, working_dir: str, llm: BaseLLMClient, embedding: BaseEmbeddingClient, embedding_dim: int, embedding_model: str) -> None:
        try:
            from lightrag import LightRAG
            from lightrag.utils import EmbeddingFunc
        except ImportError as exc:
            raise RuntimeError("LightRAG backend requires: pip install lightrag-hku") from exc
        self._llm = llm
        self._embedding = embedding
        self.rag = LightRAG(
            working_dir=working_dir,
            graph_storage="NetworkXStorage",
            llm_model_func=self._complete,
            embedding_func=EmbeddingFunc(embedding_dim=embedding_dim, func=self._embed, model_name=embedding_model),
        )

    async def _complete(self, prompt: str, **_: Any) -> str:
        return self._llm.generate(prompt)

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedding.embed_texts(texts)

    async def index(self, texts: list[str]) -> None:
        for text in texts:
            await self.rag.ainsert(text)

    async def query(self, query: str) -> str:
        try:
            from lightrag import QueryParam
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("LightRAG backend requires: pip install lightrag-hku") from exc
        return await self.rag.aquery(query, param=QueryParam(mode="hybrid"))
