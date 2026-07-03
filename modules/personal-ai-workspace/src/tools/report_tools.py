from __future__ import annotations

from typing import Any

from src.reporting.weekly_report import generate_daily_report, generate_weekly_report
from src.tools.kb_tools import search_kb_tool
from src.tools.todo_tools import read_todo_tool


def weekly_report_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    todo = read_todo_tool(config, {"path": args.get("todo", "todo.md")})
    evidence = search_kb_tool(config, {"query": args.get("query", "本周 进展 风险 计划"), "collection": args.get("collection"), "top_k": 5}).get("results", [])
    return {"success": True, "report": generate_weekly_report(todo.get("tasks", []), evidence, args.get("from", ""), args.get("to", ""))}


def daily_report_tool(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    todo = read_todo_tool(config, {"path": args.get("todo", "todo.md")})
    evidence = search_kb_tool(config, {"query": args.get("query", "今日 完成 风险 明日"), "collection": args.get("collection"), "top_k": 5}).get("results", [])
    return {"success": True, "report": generate_daily_report(todo.get("tasks", []), evidence, args.get("date", ""))}

