from __future__ import annotations

import json
import sys
from typing import Any, Callable

from src.config.config_loader import load_config
from src.observability.trace_logger import JsonlLogger
from src.tools.default_registry import build_registry
from src.tools.tool_registry import ToolRegistry


SUPPORTED_TOOLS = {
    "search_kb",
    "ask_kb",
    "list_docs",
    "summarize_doc",
    "write_note",
    "generate_weekly_report",
}


def build_fastmcp_server(config: dict[str, Any] | None = None):
    """Build the official MCP SDK server over the workspace ToolRegistry."""
    from mcp.server.fastmcp import FastMCP

    config = config or load_config()
    registry = build_registry(config)
    enabled = set(config.get("mcp", {}).get("exposed_tools", SUPPORTED_TOOLS))
    unsupported = enabled - SUPPORTED_TOOLS
    if unsupported:
        raise ValueError(f"Unsupported MCP exposed_tools: {', '.join(sorted(unsupported))}")

    mcp = FastMCP(
        config.get("mcp", {}).get("server_name", "personal-ai-workspace-mcp"),
        instructions=(
            "Use ScholarMind local tools only for evidence-grounded work. "
            "Cite knowledge-base evidence and keep write_note in dry-run mode "
            "until the user explicitly confirms execution."
        ),
    )

    def register(name: str, function: Callable[..., dict[str, Any]], description: str) -> None:
        if name in enabled:
            mcp.tool(name=name, description=description)(function)

    def search_kb(
        query: str,
        collection: str | None = None,
        top_k: int = 5,
        mode: str = "hybrid",
        query_rewrite: str | None = None,
        crag_enabled: bool | None = None,
        multi_hop_enabled: bool | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "search_kb",
            {
                "query": query,
                "collection": collection,
                "top_k": top_k,
                "mode": mode,
                "query_rewrite": query_rewrite,
                "crag_enabled": crag_enabled,
                "multi_hop_enabled": multi_hop_enabled,
            },
        )

    def ask_kb(
        query: str,
        collection: str | None = None,
        top_k: int = 5,
        query_rewrite: str | None = None,
        crag_enabled: bool | None = None,
        multi_hop_enabled: bool | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "ask_kb",
            {
                "query": query,
                "collection": collection,
                "top_k": top_k,
                "query_rewrite": query_rewrite,
                "crag_enabled": crag_enabled,
                "multi_hop_enabled": multi_hop_enabled,
            },
        )

    def list_docs(collection: str | None = None) -> dict[str, Any]:
        return registry.call("list_docs", {"collection": collection})

    def summarize_doc(doc_id: str, collection: str | None = None) -> dict[str, Any]:
        return registry.call("summarize_doc", {"doc_id": doc_id, "collection": collection})

    def write_note(path: str, content: str, dry_run: bool = True, confirm: bool = False) -> dict[str, Any]:
        return registry.call("write_note", {"path": path, "content": content, "dry_run": dry_run, "confirm": confirm})

    def generate_weekly_report(
        date_from: str = "",
        date_to: str = "",
        collection: str | None = "notes",
        todo: str = "todo.md",
        query: str | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "generate_weekly_report",
            {"from": date_from, "to": date_to, "collection": collection, "todo": todo, "query": query},
        )

    register("search_kb", search_kb, "Search local knowledge-base evidence with keyword, semantic, or hybrid retrieval.")
    register("ask_kb", ask_kb, "Answer from local knowledge-base evidence and return citations and confidence.")
    register("list_docs", list_docs, "List indexed documents, optionally restricted to a collection.")
    register("summarize_doc", summarize_doc, "Generate an evidence-bound summary for one indexed document.")
    register("write_note", write_note, "Plan or write a Markdown note. Dry-run is on by default and execution requires confirmation.")
    register("generate_weekly_report", generate_weekly_report, "Generate a weekly report from todo items and local knowledge-base evidence.")

    @mcp.resource("scholarmind://collections", mime_type="application/json")
    def collections_resource() -> str:
        return json.dumps(registry.call("list_docs", {}), ensure_ascii=False)

    @mcp.resource("scholarmind://documents/{collection}", mime_type="application/json")
    def documents_resource(collection: str) -> str:
        return json.dumps(registry.call("list_docs", {"collection": collection}), ensure_ascii=False)

    @mcp.resource("scholarmind://document/{doc_id}", mime_type="application/json")
    def document_resource(doc_id: str) -> str:
        return json.dumps(registry.call("summarize_doc", {"doc_id": doc_id}), ensure_ascii=False)

    @mcp.resource("scholarmind://logs/recent", mime_type="application/json")
    def recent_logs_resource() -> str:
        return json.dumps({"recent_tool_calls": JsonlLogger(config, "tool_calls.jsonl").tail(20)}, ensure_ascii=False)

    @mcp.prompt(name="grounded-rag-answer")
    def grounded_rag_answer(question: str, collection: str | None = None) -> str:
        scope = f" in collection '{collection}'" if collection else ""
        return f"Answer this question{scope} only from ScholarMind evidence, cite each factual claim, and refuse unsupported conclusions: {question}"

    @mcp.prompt(name="research-summary")
    def research_summary(topic: str, collection: str | None = None) -> str:
        scope = f" in collection '{collection}'" if collection else ""
        return f"Search ScholarMind{scope} for {topic}, then write a concise evidence-grounded research summary with citations."

    @mcp.prompt(name="safe-note-writing")
    def safe_note_writing(path: str = "notes/new_note.md") -> str:
        return f"Draft a note for {path}, first call write_note with dry_run=true, show the plan, and request explicit confirmation before execution."

    return mcp


def serve_stdio(config: dict[str, Any] | None = None) -> None:
    """Serve production MCP traffic through the official SDK stdio transport."""
    build_fastmcp_server(config).run(transport="stdio")


def serve_legacy_json_stdio(config: dict[str, Any] | None = None) -> None:
    """Compatibility diagnostic only; production callers must use FastMCP."""
    registry = build_registry(config or load_config())
    print(json.dumps({"mode": "legacy-json-stdio", "tools": registry.list_tools()}, ensure_ascii=False), flush=True)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request.get("method") == "tools/list":
                response = {"success": True, "tools": registry.list_tools()}
            elif request.get("method") == "tools/call":
                response = registry.call(request["tool"], request.get("arguments", {}))
            else:
                response = {"success": False, "error": f"Unknown method: {request.get('method')}"}
        except Exception as exc:
            response = {"success": False, "error": str(exc)}
        print(json.dumps(response, ensure_ascii=False), flush=True)
