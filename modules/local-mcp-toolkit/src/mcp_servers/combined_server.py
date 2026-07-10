from __future__ import annotations

import json
from pathlib import Path

from src.config.config_loader import load_config, resolve_path
from src.rag.adapters import get_knowledge_base
from src.safety.audit_log import JsonlLog
from src.safety.path_guard import PathGuard
from src.tools.code_tools import CodeTools
from src.tools.filesystem_tools import FilesystemTools
from src.tools.rag_tools import RagTools
from src.tools.registry import ToolRegistry
from src.tools.schemas import ToolSpec, schema


def build_registry(config: dict | None = None, enabled: list[str] | None = None) -> ToolRegistry:
    config = config or load_config()
    enabled = enabled or config["mcp"].get("enabled_servers", ["rag", "filesystem", "code"])
    tool_log = JsonlLog(resolve_path(config, config["logging"]["tool_call_log"]))
    security_log = JsonlLog(resolve_path(config, config["logging"]["security_audit_log"]))
    guard = PathGuard(
        resolve_path(config, config["app"]["workspace_dir"]),
        block_symlink_escape=config["security"]["block_symlink_escape"],
        block_hidden_dirs=config["security"]["block_hidden_dirs"],
        block_sensitive_files=config["security"]["block_sensitive_files"],
    )
    registry = ToolRegistry(tool_log, security_log)

    def reg(spec: ToolSpec, fn) -> None:
        registry.register(spec, fn)

    if "filesystem" in enabled:
        fs = FilesystemTools(guard, security_log, config["filesystem"]["allowed_extensions"], config["filesystem"]["max_read_chars"])
        reg(ToolSpec("list_files", "List files inside workspace", schema(properties={"path": {"type": "string"}, "recursive": {"type": "boolean"}, "extensions": {"type": "array"}, "limit": {"type": "integer"}}), None, "low", False, "filesystem"), fs.list_files)
        reg(ToolSpec("read_file", "Read a text file inside workspace", schema(["path"], {"path": {"type": "string"}, "max_chars": {"type": "integer"}}), None, "low", False, "filesystem"), fs.read_file)
        reg(ToolSpec("search_files", "Search filenames and content inside workspace", schema(["query"], {"query": {"type": "string"}, "path": {"type": "string"}, "search_content": {"type": "boolean"}, "extensions": {"type": "array"}, "limit": {"type": "integer"}}), None, "low", False, "filesystem"), fs.search_files)
        reg(ToolSpec("write_file", "Write file inside workspace with dry-run and confirm", schema(["path", "content"], {"path": {"type": "string"}, "content": {"type": "string"}, "overwrite": {"type": "boolean"}, "dry_run": {"type": "boolean"}, "confirm": {"type": "boolean"}}), None, "high", True, "filesystem"), fs.write_file)

    if "rag" in enabled:
        rag = RagTools(get_knowledge_base(config), guard, security_log)
        reg(ToolSpec("search_documents", "Search local knowledge base chunks", schema(["query"], {"query": {"type": "string"}, "collection": {"type": "string"}, "top_k": {"type": "integer"}, "filters": {"type": "object"}}), None, "low", False, "rag"), rag.search_documents)
        reg(ToolSpec("ask_knowledge_base", "Answer with KB evidence", schema(["question"], {"question": {"type": "string"}, "collection": {"type": "string"}, "top_k": {"type": "integer"}, "require_citations": {"type": "boolean"}}), None, "low", False, "rag"), rag.ask_knowledge_base)
        reg(ToolSpec("list_collections", "List KB collections", schema(), None, "low", False, "rag"), rag.list_collections)
        reg(ToolSpec("list_documents", "List KB documents", schema(properties={"collection": {"type": "string"}, "doc_type": {"type": "string"}, "limit": {"type": "integer"}}), None, "low", False, "rag"), rag.list_documents)
        reg(ToolSpec("get_document_summary", "Get document summary", schema(["doc_id"], {"doc_id": {"type": "string"}}), None, "low", False, "rag"), rag.get_document_summary)
        reg(ToolSpec("add_document", "Add document to KB", schema(["file_path"], {"file_path": {"type": "string"}, "collection": {"type": "string"}, "tags": {"type": "array"}, "dry_run": {"type": "boolean"}, "confirm": {"type": "boolean"}}), None, "medium", True, "rag"), rag.add_document)
        reg(ToolSpec("delete_document", "Delete KB record and index", schema(["doc_id"], {"doc_id": {"type": "string"}, "dry_run": {"type": "boolean"}, "confirm": {"type": "boolean"}}), None, "high", True, "rag"), rag.delete_document)

    if "code" in enabled:
        code = CodeTools(guard, config["code"]["ignored_dirs"], config["code"]["allowed_code_extensions"])
        reg(ToolSpec("list_repo_tree", "List repository tree", schema(["repo_path"], {"repo_path": {"type": "string"}, "max_depth": {"type": "integer"}, "include_files": {"type": "boolean"}}), None, "low", False, "code"), code.list_repo_tree)
        reg(ToolSpec("search_code", "Search code content", schema(["repo_path", "query"], {"repo_path": {"type": "string"}, "query": {"type": "string"}, "extensions": {"type": "array"}, "limit": {"type": "integer"}}), None, "low", False, "code"), code.search_code)
        reg(ToolSpec("read_code_file", "Read code file", schema(["repo_path", "file_path"], {"repo_path": {"type": "string"}, "file_path": {"type": "string"}, "max_chars": {"type": "integer"}}), None, "low", False, "code"), code.read_code_file)
        reg(ToolSpec("summarize_module", "Summarize module", schema(["repo_path", "module_path"], {"repo_path": {"type": "string"}, "module_path": {"type": "string"}, "max_files": {"type": "integer"}}), None, "low", False, "code"), code.summarize_module)
        reg(ToolSpec("find_todos", "Find TODO markers", schema(["repo_path"], {"repo_path": {"type": "string"}, "markers": {"type": "array"}}), None, "low", False, "code"), code.find_todos)
        reg(ToolSpec("generate_repo_summary", "Generate repository summary", schema(["repo_path"], {"repo_path": {"type": "string"}, "max_depth": {"type": "integer"}}), None, "low", False, "code"), code.generate_repo_summary)
        reg(ToolSpec("generate_issue_draft", "Generate issue draft", schema(["title_hint", "context"], {"title_hint": {"type": "string"}, "context": {"type": "string"}, "related_files": {"type": "array"}}), None, "low", False, "code"), code.generate_issue_draft)
        reg(ToolSpec("generate_pr_description", "Generate PR description", schema(["change_summary"], {"change_summary": {"type": "string"}, "files_changed": {"type": "array"}, "testing_notes": {"type": "string"}}), None, "low", False, "code"), code.generate_pr_description)

    return registry


def run_stdio_server(registry: ToolRegistry) -> None:
    try:
        run_fastmcp_server(registry)
    except ImportError as exc:
        raise RuntimeError("Official MCP SDK is required for production serving. Install with: pip install 'mcp>=1.9.0'") from exc


def run_legacy_stdio_server(registry: ToolRegistry) -> None:
    """Compatibility-only JSON-lines server; never used by production `serve`."""
    print(json.dumps({"server": "local-mcp-toolkit", "mode": "minimal-json-stdio", "tools": registry.list_tools()}, ensure_ascii=False), flush=True)
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            continue
        req = json.loads(line)
        if req.get("method") == "tools/list":
            print(json.dumps({"tools": registry.list_tools()}, ensure_ascii=False), flush=True)
        elif req.get("method") == "tools/call":
            print(json.dumps(registry.call(req["tool"], req.get("arguments", {})), ensure_ascii=False), flush=True)
        else:
            print(json.dumps({"success": False, "error": "unknown method"}, ensure_ascii=False), flush=True)


def run_fastmcp_server(registry: ToolRegistry) -> None:
    build_fastmcp_server(registry).run()


def build_fastmcp_server(registry: ToolRegistry):
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("local-mcp-toolkit")

    @mcp.tool()
    def list_files(path: str = ".", recursive: bool = False, extensions: list[str] | None = None, limit: int = 100) -> dict:
        return registry.call("list_files", {"path": path, "recursive": recursive, "extensions": extensions, "limit": limit})

    @mcp.tool()
    def read_file(path: str, max_chars: int = 8000) -> dict:
        return registry.call("read_file", {"path": path, "max_chars": max_chars})

    @mcp.tool()
    def search_files(query: str, path: str = ".", search_content: bool = True, extensions: list[str] | None = None, limit: int = 50) -> dict:
        return registry.call("search_files", {"query": query, "path": path, "search_content": search_content, "extensions": extensions, "limit": limit})

    @mcp.tool()
    def write_file(path: str, content: str, overwrite: bool = False, dry_run: bool = True, confirm: bool = False) -> dict:
        return registry.call("write_file", {"path": path, "content": content, "overwrite": overwrite, "dry_run": dry_run, "confirm": confirm})

    @mcp.tool()
    def search_documents(query: str, collection: str | None = None, top_k: int = 5, filters: dict | None = None) -> dict:
        return registry.call("search_documents", {"query": query, "collection": collection, "top_k": top_k, "filters": filters})

    @mcp.tool()
    def ask_knowledge_base(question: str, collection: str | None = None, top_k: int = 5, require_citations: bool = True) -> dict:
        return registry.call("ask_knowledge_base", {"question": question, "collection": collection, "top_k": top_k, "require_citations": require_citations})

    @mcp.tool()
    def list_collections() -> dict:
        return registry.call("list_collections", {})

    @mcp.tool()
    def list_documents(collection: str | None = None, doc_type: str | None = None, limit: int = 50) -> dict:
        return registry.call("list_documents", {"collection": collection, "doc_type": doc_type, "limit": limit})

    @mcp.tool()
    def get_document_summary(doc_id: str) -> dict:
        return registry.call("get_document_summary", {"doc_id": doc_id})

    @mcp.tool()
    def add_document(file_path: str, collection: str = "default", tags: list[str] | None = None, dry_run: bool = True, confirm: bool = False) -> dict:
        return registry.call("add_document", {"file_path": file_path, "collection": collection, "tags": tags, "dry_run": dry_run, "confirm": confirm})

    @mcp.tool()
    def delete_document(doc_id: str, dry_run: bool = True, confirm: bool = False) -> dict:
        return registry.call("delete_document", {"doc_id": doc_id, "dry_run": dry_run, "confirm": confirm})

    @mcp.tool()
    def list_repo_tree(repo_path: str, max_depth: int = 3, include_files: bool = True) -> dict:
        return registry.call("list_repo_tree", {"repo_path": repo_path, "max_depth": max_depth, "include_files": include_files})

    @mcp.tool()
    def search_code(repo_path: str, query: str, extensions: list[str] | None = None, limit: int = 50) -> dict:
        return registry.call("search_code", {"repo_path": repo_path, "query": query, "extensions": extensions, "limit": limit})

    @mcp.tool()
    def read_code_file(repo_path: str, file_path: str, max_chars: int = 12000) -> dict:
        return registry.call("read_code_file", {"repo_path": repo_path, "file_path": file_path, "max_chars": max_chars})

    @mcp.tool()
    def summarize_module(repo_path: str, module_path: str, max_files: int = 20) -> dict:
        return registry.call("summarize_module", {"repo_path": repo_path, "module_path": module_path, "max_files": max_files})

    @mcp.tool()
    def find_todos(repo_path: str, markers: list[str] | None = None) -> dict:
        return registry.call("find_todos", {"repo_path": repo_path, "markers": markers})

    @mcp.tool()
    def generate_repo_summary(repo_path: str, max_depth: int = 3) -> dict:
        return registry.call("generate_repo_summary", {"repo_path": repo_path, "max_depth": max_depth})

    @mcp.tool()
    def generate_issue_draft(title_hint: str, context: str, related_files: list[str] | None = None) -> dict:
        return registry.call("generate_issue_draft", {"title_hint": title_hint, "context": context, "related_files": related_files})

    @mcp.tool()
    def generate_pr_description(change_summary: str, files_changed: list[str] | None = None, testing_notes: str = "") -> dict:
        return registry.call("generate_pr_description", {"change_summary": change_summary, "files_changed": files_changed, "testing_notes": testing_notes})

    @mcp.resource("scholarmind://collections")
    def collections_resource() -> str:
        return json.dumps(registry.call("list_collections", {}), ensure_ascii=False)

    @mcp.resource("scholarmind://documents/{collection}")
    def documents_resource(collection: str) -> str:
        return json.dumps(registry.call("list_documents", {"collection": collection}), ensure_ascii=False)

    @mcp.resource("scholarmind://document/{doc_id}")
    def document_resource(doc_id: str) -> str:
        return json.dumps(registry.call("get_document_summary", {"doc_id": doc_id}), ensure_ascii=False)

    @mcp.resource("scholarmind://logs/recent")
    def recent_logs_resource() -> str:
        return json.dumps({"recent_tool_calls": registry.tool_log.read(20)}, ensure_ascii=False)

    @mcp.prompt()
    def grounded_rag_answer(question: str) -> str:
        return f"Answer this question only from ScholarMind evidence and cite every claim: {question}"

    @mcp.prompt()
    def research_summary(topic: str) -> str:
        return f"Search ScholarMind for {topic}, then write a concise evidence-grounded research summary."

    @mcp.prompt()
    def safe_file_organization(path: str = ".") -> str:
        return f"Inspect {path}, produce a dry-run organization plan, and request confirmation before any write."

    return mcp
