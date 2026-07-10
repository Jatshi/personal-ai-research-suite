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
        self._initialized = False

        # LightRAG serializes its configuration with dataclasses.asdict(). Bound
        # adapter methods would deep-copy this instance (and runtime ContextVars),
        # so callbacks must not retain the adapter as ``__self__``.
        async def complete(prompt: str, **_: Any) -> str:
            return llm.generate(prompt)

        async def embed(texts: list[str]) -> list[list[float]]:
            # LightRAG validates ``.size`` and requires an ndarray even though
            # the workspace's BaseEmbeddingClient intentionally returns lists.
            import numpy as np

            return np.asarray(embedding.embed_texts(texts), dtype=np.float32)

        self.rag = LightRAG(
            working_dir=working_dir,
            graph_storage="NetworkXStorage",
            llm_model_func=complete,
            embedding_func=EmbeddingFunc(embedding_dim=embedding_dim, func=embed, model_name=embedding_model),
        )

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await self.rag.initialize_storages()
            self._initialized = True

    async def index(self, texts: list[str]) -> None:
        await self._ensure_initialized()
        for text in texts:
            await self.rag.ainsert(text)

    async def query(self, query: str) -> str:
        try:
            from lightrag import QueryParam
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("LightRAG backend requires: pip install lightrag-hku") from exc
        await self._ensure_initialized()
        return await self.rag.aquery(query, param=QueryParam(mode="hybrid"))
