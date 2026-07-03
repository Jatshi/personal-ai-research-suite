from __future__ import annotations

from typing import Any

from src.generation.factory import build_llm_client
from src.observability.llm_logger import log_llm_call
from src.grounding.citation_builder import build_citations
from src.grounding.evidence_checker import NO_EVIDENCE, has_enough_evidence


def generate_grounded_answer(query: str, chunks: list[dict[str, Any]], min_confidence: float, config: dict[str, Any] | None = None) -> dict[str, Any]:
    ok, confidence = has_enough_evidence(query, chunks, min_confidence)
    citations = build_citations(chunks if ok else [])
    if not ok:
        return {"answer": NO_EVIDENCE, "confidence": confidence, "citations": [], "evidence": chunks}
    llm = build_llm_client(config or {"llm": {"backend": "mock"}})
    prompt = (
        "请基于 evidence chunks 回答用户问题。回答必须可追溯到证据；"
        f"如果证据不足，只回答：{NO_EVIDENCE}\n\n用户问题：{query}"
    )
    try:
        answer = llm.generate(prompt, chunks)
        if config:
            log_llm_call(config, prompt, answer, backend=str(config.get("llm", {}).get("backend", "mock")))
    except Exception as exc:
        answer = f"LLM 调用失败：{exc}"
        if config:
            log_llm_call(config, prompt, answer, backend=str(config.get("llm", {}).get("backend", "unknown")), success=False, error=str(exc))
        return {"answer": answer, "confidence": confidence, "citations": citations, "evidence": chunks, "llm_error": str(exc)}
    return {"answer": answer, "confidence": confidence, "citations": citations, "evidence": chunks}
