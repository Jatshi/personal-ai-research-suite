from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.tools.kb_tools import ask_kb_tool


def eval_ragas(config: dict[str, Any], dataset: str) -> dict[str, Any]:
    """Run RAGAS with OpenAI-compatible evaluator clients when optional deps exist."""
    try:
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics.collections import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except ImportError as exc:
        raise RuntimeError("RAGAS evaluation requires production extras: pip install -e '.[production]'") from exc

    llm_cfg = config["llm"]
    emb_cfg = config["embedding"]
    api_key = os.getenv(llm_cfg.get("api_key_env", "OPENAI_API_KEY"))
    if not api_key:
        raise RuntimeError(f"Missing evaluator API key: {llm_cfg.get('api_key_env', 'OPENAI_API_KEY')}")
    base_url = os.getenv(llm_cfg.get("base_url_env", "OPENAI_BASE_URL"))
    chat = ChatOpenAI(model=llm_cfg["model_name"], api_key=api_key, base_url=base_url, temperature=0)
    embeddings = OpenAIEmbeddings(model=emb_cfg["model_name"], api_key=api_key, base_url=base_url)
    samples = []
    for line in Path(dataset).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        response = ask_kb_tool(config, {"query": item["question"], "collection": item.get("collection"), "top_k": 5})
        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                response=response["answer"],
                retrieved_contexts=[chunk.get("text", "") for chunk in response.get("evidence", [])],
                reference=item.get("reference") or "",
            )
        )
    result = evaluate(
        dataset=EvaluationDataset(samples=samples),
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
        llm=LangchainLLMWrapper(chat),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
    )
    return {"engine": "ragas", "metrics": result.to_pandas().mean(numeric_only=True).to_dict(), "case_count": len(samples)}
