from __future__ import annotations


class LiteratureTableGenerator:
    def generate(self, papers: list[dict]) -> str:
        lines = ["| Title | Year | Task | Method | Dataset | Metric | Main Result | Limitation | Relevance |", "|---|---:|---|---|---|---|---|---|---|"]
        for p in papers:
            sec = p.get("sections", {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._cell(p.get("title", p.get("filename", ""))),
                        self._cell(p.get("year", "")),
                        self._cell((sec.get("introduction") or p.get("abstract") or "")[:120]),
                        self._cell((sec.get("method") or "")[:120]),
                        "See evidence",
                        "See evidence",
                        self._cell((sec.get("experiment") or sec.get("conclusion") or "")[:120]),
                        self._cell((sec.get("discussion") or "")[:120]),
                        "Personal academic knowledge base",
                    ]
                )
                + " |"
            )
        return "\n".join(lines)

    @staticmethod
    def _cell(value: str) -> str:
        return str(value).replace("|", "/").replace("\n", " ").strip()

