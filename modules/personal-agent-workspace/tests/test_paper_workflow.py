from __future__ import annotations

from pathlib import Path

from src.tools.paper_tools import run_paper_reading_workflow


def test_paper_workflow_generates_notes(cfg: dict) -> None:
    out = Path(cfg["app"]["workspace_dir"]) / "data" / "exports" / "paper_notes"
    result = run_paper_reading_workflow(f"{cfg['app']['workspace_dir']}/papers", out)
    assert result["papers"]
    assert (out / "literature_review_table.md").exists()
    assert list(out.glob("*_reading_note.md"))

