from __future__ import annotations

import json
import re
from pathlib import Path

from src.tools.document_tools import read_document
from src.utils.text_utils import clean_text


def read_paper(path: str) -> dict:
    text = read_document(path)["text"]
    lines = [l.strip("# ").strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else Path(path).stem
    authors = []
    for l in lines[:8]:
        if l.lower().startswith("authors"):
            authors = [x.strip() for x in re.split(r",| and ", l.split(":", 1)[-1]) if x.strip()]
    year = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    keywords = []
    kw = re.search(r"keywords?\s*:\s*(.+)", text, re.I)
    if kw:
        keywords = [x.strip() for x in re.split(r"[,;，；]", kw.group(1)) if x.strip()]
    return {"path": path, "text": text, "title": title, "authors": authors, "year": year.group(1) if year else "", "keywords": keywords, "sections": split_sections(text)}


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "overview"
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if m:
            title = m.group(1).lower()
            if "method" in title:
                current = "method"
            elif "experiment" in title or "result" in title:
                current = "experiment"
            elif "discussion" in title or "limitation" in title:
                current = "discussion"
            elif "conclusion" in title:
                current = "conclusion"
            elif "abstract" in title or "introduction" in title:
                current = "introduction"
            else:
                current = title[:40]
        sections[current] = (sections.get(current, "") + "\n" + line).strip()
    return sections


def run_paper_reading_workflow(path: str, output: str | Path) -> dict:
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in Path(path).rglob("*") if p.suffix.lower() in {".md", ".pdf"}])
    log = []
    papers = []
    for file in files:
        state = {"file": str(file), "steps": {}, "errors": []}
        try:
            paper = read_paper(str(file))
            state["steps"]["reader"] = {k: paper[k] for k in ["title", "authors", "year", "keywords"]}
            method = clean_text(paper["sections"].get("method", ""))[:800]
            state["steps"]["method"] = {"summary": method, "innovation": "Mock extraction based on method section."}
            exp = clean_text(paper["sections"].get("experiment", ""))[:800]
            state["steps"]["experiment"] = {"summary": exp, "dataset": "See evidence", "metrics": "See evidence", "baselines": "See evidence"}
            discussion = clean_text(paper["sections"].get("discussion", ""))[:800]
            state["steps"]["critic"] = {"limitations": discussion or "Not explicitly found.", "reproducibility": "Check datasets, metrics, and code availability."}
            note = paper_note_markdown(paper, state)
            note_path = output_dir / f"{Path(file).stem}_reading_note.md"
            note_path.write_text(note, encoding="utf-8")
            state["steps"]["writer"] = {"note_path": str(note_path)}
            papers.append({**paper, "note_path": str(note_path), "state": state})
        except Exception as exc:
            state["errors"].append(str(exc))
            state["status"] = "failed"
        else:
            state["status"] = "completed"
        log.append(state)
    table = literature_table(papers)
    (output_dir / "literature_review_table.md").write_text(table, encoding="utf-8")
    (output_dir / "workflow_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"papers": papers, "table": table, "log": log, "output_dir": str(output_dir)}


def paper_note_markdown(paper: dict, state: dict) -> str:
    steps = state["steps"]
    return f"""# Paper Reading Note

## Basic Information
- Title: {paper.get('title', '')}
- Authors: {', '.join(paper.get('authors', []))}
- Year: {paper.get('year', '')}
- Keywords: {', '.join(paper.get('keywords', []))}

## Research Question
{clean_text(paper.get('sections', {}).get('introduction', paper.get('text', '')))[:500]}

## Method Summary
{steps.get('method', {}).get('summary', '')}

## Experiments
- Dataset: {steps.get('experiment', {}).get('dataset', '')}
- Metrics: {steps.get('experiment', {}).get('metrics', '')}
- Baselines: {steps.get('experiment', {}).get('baselines', '')}
- Main Results: {steps.get('experiment', {}).get('summary', '')}

## Contributions
{steps.get('method', {}).get('innovation', '')}

## Limitations
{steps.get('critic', {}).get('limitations', '')}

## Reproducibility Notes
{steps.get('critic', {}).get('reproducibility', '')}

## Possible Extensions
Extend evaluation, compare stronger baselines, and add ablation studies.

## Key Evidence
Source: {paper.get('path', '')}
"""


def literature_table(papers: list[dict]) -> str:
    rows = ["| Title | Year | Task | Method | Dataset | Metric | Main Result | Limitation | Relevance |", "|---|---:|---|---|---|---|---|---|---|"]
    for p in papers:
        sec = p.get("sections", {})
        rows.append(f"| {p.get('title','').replace('|','/')} | {p.get('year','')} | {clean_text(sec.get('introduction',''))[:80]} | {clean_text(sec.get('method',''))[:80]} | See evidence | See evidence | {clean_text(sec.get('experiment',''))[:80]} | {clean_text(sec.get('discussion',''))[:80]} | local reading workflow |")
    return "\n".join(rows)
