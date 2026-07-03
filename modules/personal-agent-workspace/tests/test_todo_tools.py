from __future__ import annotations

from src.tools.todo_tools import read_todo


def test_todo_parser(cfg: dict) -> None:
    result = read_todo(f"{cfg['app']['workspace_dir']}/todo.md")
    assert result["tasks"]
    assert result["open"]
    assert result["completed"]

