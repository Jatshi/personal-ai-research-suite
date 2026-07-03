from __future__ import annotations

from src.generation.llm_client import BaseLLMClient
from src.generation.mock_llm import INSUFFICIENT_EVIDENCE_MESSAGE
from src.generation.prompts import ANSWER_PROMPT
from src.grounding.citation_builder import build_citations
from src.grounding.evidence_checker import has_sufficient_evidence
from src.models import Answer, SearchResult


class AnswerGenerator:
    def __init__(self, llm: BaseLLMClient, min_confidence: float = 0.35) -> None:
        self.llm = llm
        self.min_confidence = min_confidence

    def answer(self, query: str, results: list[SearchResult]) -> Answer:
        ok, confidence = has_sufficient_evidence(query, results, self.min_confidence)
        if not ok:
            return Answer(INSUFFICIENT_EVIDENCE_MESSAGE, [], confidence, results)
        context = [{"text": r.chunk.text, "chunk_id": r.chunk.chunk_id, **r.chunk.metadata} for r in results]
        text = self.llm.generate(ANSWER_PROMPT.format(query=query), context=context)
        citations = build_citations(results)
        return Answer(text=f"{text}\n\n" + "\n".join(citations), citations=citations, confidence=confidence, evidence=results)
