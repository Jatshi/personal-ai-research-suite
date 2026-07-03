from __future__ import annotations

from src.models import Chunk


class PaperNoteGenerator:
    def generate(self, metadata: dict, sections: dict[str, str], chunks: list[Chunk] | None = None) -> str:
        chunks = chunks or []
        evidence = "\n".join(
            f"{i+1}. Source: {c.metadata.get('filename')}, page {c.metadata.get('page') or 'N/A'}, chunk_id={c.chunk_id}"
            for i, c in enumerate(chunks[:5])
        )
        method = sections.get("method", "")[:700]
        experiment = sections.get("experiment", "")[:700]
        intro = sections.get("introduction", metadata.get("abstract", ""))[:700]
        conclusion = sections.get("conclusion", "")[:700]
        return f"""# Paper Reading Note

## Basic Information
- Title: {metadata.get('title', '')}
- Authors: {', '.join(metadata.get('authors', []))}
- Year: {metadata.get('year', '')}
- Venue: {metadata.get('venue', '')}
- Keywords: {', '.join(metadata.get('keywords', []))}

## Research Question
{intro}

## Method
{method}

## Experiments
- Dataset: See evidence chunks.
- Metrics: See evidence chunks.
- Baselines: See evidence chunks.

{experiment}

## Main Results
{conclusion or experiment}

## Contributions
Derived from the abstract, introduction, and method evidence above.

## Limitations
{sections.get('discussion', '')[:700]}

## Reproducibility Notes
Check whether datasets, metrics, baselines, and implementation details are explicitly available in the cited chunks.

## Key Evidence
{evidence}
"""

