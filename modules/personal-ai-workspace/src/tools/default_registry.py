from __future__ import annotations

from typing import Any

from src.tools.file_tools import list_files_tool, read_file_tool
from src.tools.kb_tools import ask_kb_tool, ingest_tool, list_docs_tool, search_kb_tool, summarize_doc_tool
from src.tools.note_tools import write_note_tool
from src.tools.report_tools import daily_report_tool, weekly_report_tool
from src.tools.todo_tools import read_todo_tool, write_todo_tool
from src.tools.tool_registry import ToolRegistry, ToolSpec


def build_registry(config: dict[str, Any]) -> ToolRegistry:
    r = ToolRegistry(config)
    r.register(ToolSpec("ingest", "Import documents", {"path": "str", "collection": "str"}, category="kb"), lambda a: ingest_tool(config, a))
    r.register(ToolSpec("search_kb", "Search knowledge base", {"query": "str"}, category="kb"), lambda a: search_kb_tool(config, a))
    r.register(ToolSpec("ask_kb", "Ask knowledge base", {"query": "str"}, category="kb"), lambda a: ask_kb_tool(config, a))
    r.register(ToolSpec("list_docs", "List documents", {"collection": "str"}, category="kb"), lambda a: list_docs_tool(config, a))
    r.register(ToolSpec("summarize_doc", "Summarize document", {"doc_id": "str"}, category="kb"), lambda a: summarize_doc_tool(config, a))
    r.register(ToolSpec("list_files", "List workspace files", {"path": "str"}, category="filesystem"), lambda a: list_files_tool(config, a))
    r.register(ToolSpec("read_file", "Read workspace file", {"path": "str"}, category="filesystem"), lambda a: read_file_tool(config, a))
    r.register(ToolSpec("write_note", "Write markdown note", {"path": "str", "content": "str"}, risk_level="high", requires_confirmation=True, category="notes"), lambda a: write_note_tool(config, a))
    r.register(ToolSpec("read_todo", "Read todo.md", {"path": "str"}, category="todo"), lambda a: read_todo_tool(config, a))
    r.register(ToolSpec("write_todo", "Write todo.md", {"path": "str", "content": "str"}, risk_level="high", requires_confirmation=True, category="todo"), lambda a: write_todo_tool(config, a))
    r.register(ToolSpec("generate_daily_report", "Generate daily report", {"date": "str"}, category="report"), lambda a: daily_report_tool(config, a))
    r.register(ToolSpec("generate_weekly_report", "Generate weekly report", {"from": "str", "to": "str"}, category="report"), lambda a: weekly_report_tool(config, a))
    return r

