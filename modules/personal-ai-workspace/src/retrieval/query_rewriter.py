from __future__ import annotations

from dataclasses import dataclass

from src.generation.llm_client import BaseLLMClient


@dataclass(frozen=True)
class QueryVariant:
    text: str
    kind: str


class QueryRewriter:
    def __init__(self, llm: BaseLLMClient, mode: str, max_subqueries: int = 3) -> None:
        self.llm = llm
        self.mode = mode
        self.max_subqueries = max_subqueries

    def rewrite(self, query: str) -> list[QueryVariant]:
        if self.mode == "hyde":
            hypothetical = self.llm.generate(
                f"Write a short hypothetical evidence passage that would answer this query. Do not add citations. Query: {query}"
            ).strip()
            return [QueryVariant(query, "original"), QueryVariant(hypothetical or query, "hyde")]
        if self.mode == "decomposition":
            raw = self.llm.generate(
                f"Break this research query into at most {self.max_subqueries} independent retrieval queries. Return one query per line. Query: {query}"
            )
            values = [line.strip("- 1234567890.\t") for line in raw.splitlines() if line.strip()]
            unique = list(dict.fromkeys([query, *values]))[: self.max_subqueries + 1]
            return [QueryVariant(value, "original" if index == 0 else "decomposition") for index, value in enumerate(unique)]
        return [QueryVariant(query, "original")]
