from __future__ import annotations

from src.tools.thesis_tools import check_figure_table_references, check_thesis_structure


def test_thesis_checker_finds_numbering_issues(cfg: dict) -> None:
    path = f"{cfg['app']['workspace_dir']}/thesis_sample/thesis.md"
    structure = check_thesis_structure(path)
    figures = check_figure_table_references(path)
    assert structure["issues"]
    assert figures["issues"]

