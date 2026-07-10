from __future__ import annotations

from typing import Any

from src.generation.llm_client import BaseLLMClient
from src.retrieval.adaptive_router import decide_route
from src.retrieval.context_compressor import compress_context
from src.retrieval.multi_hop_retriever import retrieve_multi_hop
from src.retrieval.query_rewriter import QueryRewriter


class StubLLM(BaseLLMClient):
    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        if "Break" in prompt:
            return "method A\nmethod B"
        return "hypothetical evidence"


def test_query_rewriter_supports_hyde_and_decomposition():
    llm = StubLLM()
    assert [item.kind for item in QueryRewriter(llm, "hyde").rewrite("RAG question")] == ["original", "hyde"]
    assert len(QueryRewriter(llm, "decomposition").rewrite("compare methods")) == 3


def test_context_compression_preserves_source_identity():
    chunks = [{"chunk_id": "c1", "text": "First relevant sentence. Second sentence.", "score": 1.0}]
    compressed, trace = compress_context("relevant", chunks, "token_budget", 30)
    assert compressed[0]["compressed_from_chunk_id"] == "c1"
    assert trace["after_chars"] <= 30


def test_crag_low_and_multi_hop_trace():
    assert decide_route("query", [], 0.25).route == "low"
    first = [{"chunk_id": "c1", "text": "AlphaMethod evidence", "score": 0.9}]
    results, trace = retrieve_multi_hop("compare", first, lambda query, top_k: [{"chunk_id": "c2", "text": query, "score": 0.8}], 2, 3)
    assert {item["chunk_id"] for item in results} == {"c1", "c2"}
    assert len(trace) == 2
