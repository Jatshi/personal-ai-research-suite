from __future__ import annotations

from src.llm.base import BaseLLMClient
from src.utils.text_utils import clean_text, top_keywords


class MockLLMClient(BaseLLMClient):
    def generate(self, prompt: str, context: list[dict] | None = None) -> str:
        context = context or []
        joined = clean_text(" ".join(str(item.get("text", "")) for item in context))[:1200]
        keywords = ", ".join(top_keywords(joined, 6)) if joined else "no extracted content"
        prompt_lower = prompt.lower()
        if "summary" in prompt_lower or "摘要" in prompt:
            return f"Mock mode summary: 该内容主要围绕 {keywords}。摘要仅基于已读取文件内容，不包含外部推断。"
        if "task" in prompt_lower or "任务" in prompt:
            return (
                "Mock mode task plan:\n"
                "1. 梳理输入材料和目标，priority=high。\n"
                "2. 完成最小可运行版本，priority=high。\n"
                "3. 补测试、README 和验收命令，priority=medium。\n"
                "4. 根据日志复盘风险和下一步，priority=medium。"
            )
        return f"Mock mode answer based on local context. Key signals: {keywords}."
