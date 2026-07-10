from __future__ import annotations

import json
from typing import Any

from src.generation.llm_client import BaseLLMClient, LLMToolResponse
from src.utils.text_utils import first_sentences, keyword_summary


class MockLLMClient(BaseLLMClient):
    def generate(self, prompt: str, context: list[dict[str, Any]] | None = None) -> str:
        if "tool plan" in prompt.lower() or "tool-planning" in prompt.lower() or "工具计划" in prompt:
            goal = _extract_goal(prompt)
            return json.dumps(
                {
                    "plan": [
                        "Search the local knowledge base for relevant evidence.",
                        "Generate a report using todo items and retrieved evidence.",
                    ],
                    "tool_calls": [
                        {"tool_name": "search_kb", "arguments": {"query": goal, "top_k": 3}},
                        {"tool_name": "generate_weekly_report", "arguments": {"query": goal}},
                    ],
                    "final_response_hint": "Summarize tool outputs into a concise action-oriented report.",
                },
                ensure_ascii=False,
            )

        context = context or []
        if not context:
            return "[Mock LLM] 知识库中没有足够证据回答该问题。"
        snippets = []
        for item in context[:5]:
            text = item.get("text") or item.get("snippet") or ""
            src = item.get("file_name") or item.get("title") or "unknown"
            snippets.append(f"- 来自 {src}: {first_sentences(text, 180)}")
        terms = keyword_summary(" ".join(str(i.get("text", "")) for i in context), 8)
        return "[Mock LLM] 基于检索证据的摘要：\n" + "\n".join(snippets) + f"\n\n关键词：{', '.join(terms)}"


    def complete_with_tools(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMToolResponse:
        # Mock mode intentionally takes no action. Tests can inject a scripted
        # client to exercise tool-call branches deterministically.
        prompt = "\n".join(str(message.get("content", "")) for message in messages)
        return LLMToolResponse(content=self.generate(prompt))


def _extract_goal(prompt: str) -> str:
    for marker in ["Goal:", "User goal:", "用户目标："]:
        if marker in prompt:
            return prompt.split(marker, 1)[1].splitlines()[0].strip()[:300]
    return "workspace goal"
