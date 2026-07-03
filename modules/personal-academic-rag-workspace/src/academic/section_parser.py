from __future__ import annotations

import re

from src.models import Chunk


SECTION_PATTERNS = {
    "introduction": r"\b(1\.?\s*)?introduction\b|引言",
    "related_work": r"related work|background|相关工作",
    "method": r"methodology|methods?|approach|proposed|方法",
    "experiment": r"experiments?|results?|evaluation|实验|结果",
    "discussion": r"discussion|讨论",
    "conclusion": r"conclusions?|结论",
    "references": r"references|bibliography|参考文献",
}


class SectionParser:
    def parse(self, chunks: list[Chunk]) -> dict[str, str]:
        sections = {k: "" for k in SECTION_PATTERNS}
        current = "introduction"
        for chunk in chunks:
            head = chunk.text[:300]
            for name, pat in SECTION_PATTERNS.items():
                if re.search(pat, head, flags=re.I):
                    current = name
                    chunk.metadata["section"] = name
                    break
            sections[current] = (sections.get(current, "") + "\n" + chunk.text).strip()
        return {k: v for k, v in sections.items() if v}

