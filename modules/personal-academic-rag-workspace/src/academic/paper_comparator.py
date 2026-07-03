from __future__ import annotations


class PaperComparator:
    def compare(self, papers: list[dict]) -> str:
        lines = ["# Paper Comparison", ""]
        for p in papers:
            sections = p.get("sections", {})
            lines.append(f"## {p.get('title', p.get('filename', 'Untitled'))}")
            lines.append(f"- Year: {p.get('year', '')}")
            lines.append(f"- Method: {(sections.get('method') or p.get('abstract') or '')[:500]}")
            lines.append(f"- Experiments: {(sections.get('experiment') or '')[:500]}")
            lines.append(f"- Limitation: {(sections.get('discussion') or '')[:350]}")
            lines.append("")
        return "\n".join(lines)

