from __future__ import annotations

import json
import os
import asyncio
import math
from pathlib import Path
from typing import Any

from src.tools.kb_tools import ask_kb_tool
from src.generation.factory import build_embedding_client


def normalize_ragas_metrics(values: dict[str, Any]) -> tuple[dict[str, float | None], list[str]]:
    """Convert dataframe aggregates into JSON-safe metric values."""
    metrics: dict[str, float | None] = {}
    undefined: list[str] = []
    for name, value in values.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            metrics[name] = None
            undefined.append(name)
            continue
        if math.isfinite(numeric):
            metrics[name] = numeric
        else:
            metrics[name] = None
            undefined.append(name)
    return metrics, undefined


def eval_ragas(config: dict[str, Any], dataset: str) -> dict[str, Any]:
    """Run RAGAS with OpenAI-compatible evaluator clients when optional deps exist."""
    try:
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.embeddings.base import BaseRagasEmbeddings
        from ragas.llms import LangchainLLMWrapper
        from ragas.run_config import RunConfig
        # These legacy classes are the compatible metric hierarchy for
        # ragas.evaluate() in RAGAS 0.4.x. The newer collections metrics are
        # intended for the experiment API and are not subclasses of Metric.
        from ragas.metrics._answer_relevance import AnswerRelevancy
        from ragas.metrics._context_precision import ContextPrecision
        from ragas.metrics._context_recall import ContextRecall
        from ragas.metrics._faithfulness import Faithfulness
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError("RAGAS evaluation requires production extras: pip install -e '.[production]'") from exc

    llm_cfg = config["llm"]
    emb_cfg = config["embedding"]
    api_key = os.getenv(llm_cfg.get("api_key_env", "OPENAI_API_KEY"))
    if not api_key:
        raise RuntimeError(f"Missing evaluator API key: {llm_cfg.get('api_key_env', 'OPENAI_API_KEY')}")
    base_url = os.getenv(llm_cfg.get("base_url_env", "OPENAI_BASE_URL"))
    chat = ChatOpenAI(model=llm_cfg["model_name"], api_key=api_key, base_url=base_url, temperature=0)
    # Keep the LLM wrapper for RAGAS's legacy evaluate API, but route embedding
    # calls through the workspace's proven OpenAI-compatible embedding client.
    # Some compatible providers reject the batch payload emitted by LangChain.
    workspace_embedder = build_embedding_client(config)

    class WorkspaceRagasEmbeddings(BaseRagasEmbeddings):
        def __init__(self) -> None:
            super().__init__()
            self.run_config = RunConfig()

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return workspace_embedder.embed_texts(texts)

        def embed_query(self, text: str) -> list[float]:
            return workspace_embedder.embed_query(text)

        async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
            return await asyncio.to_thread(self.embed_documents, texts)

        async def aembed_query(self, text: str) -> list[float]:
            return await asyncio.to_thread(self.embed_query, text)
    samples = []
    reference_count = 0
    skipped_refusal_cases = 0
    for line in Path(dataset).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        # RAGAS answer-quality metrics measure generated answers. Refusal cases
        # are evaluated by the deterministic refusal metric instead.
        if item.get("should_answer") is False:
            skipped_refusal_cases += 1
            continue
        reference = item.get("reference") or item.get("reference_answer") or ""
        if reference.strip():
            reference_count += 1
        response = ask_kb_tool(config, {"query": item["question"], "collection": item.get("collection"), "top_k": 5})
        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                response=response["answer"],
                retrieved_contexts=[chunk.get("text", "") for chunk in response.get("evidence", [])],
                reference=reference,
            )
        )
    ragas_llm = LangchainLLMWrapper(chat)
    ragas_embeddings = WorkspaceRagasEmbeddings()
    result = evaluate(
        dataset=EvaluationDataset(samples=samples),
        metrics=[
            Faithfulness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall(),
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )
    metrics, undefined_metrics = normalize_ragas_metrics(result.to_pandas().mean(numeric_only=True).to_dict())
    warnings: list[str] = []
    if reference_count < len(samples):
        warnings.append(
            f"Only {reference_count}/{len(samples)} samples include a non-empty reference; "
            "reference-dependent metrics can be undefined."
        )
    return {
        "engine": "ragas",
        "metrics": metrics,
        "undefined_metrics": undefined_metrics,
        "reference_count": reference_count,
        "case_count": len(samples),
        "skipped_refusal_cases": skipped_refusal_cases,
        "warnings": warnings,
    }
