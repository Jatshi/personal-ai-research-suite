from __future__ import annotations

import argparse
import importlib.util
import importlib.metadata
import json
import re

from src.config.config_loader import load_config, resolve_path
from src.mcp_servers.combined_server import build_registry, run_legacy_stdio_server, run_stdio_server
from src.safety.audit_log import JsonlLog


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("local-mcp-toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--server", choices=["combined", "rag", "filesystem", "code"], default="combined")
    legacy = sub.add_parser("legacy-serve")
    legacy.add_argument("--server", choices=["combined", "rag", "filesystem", "code"], default="combined")
    tc = sub.add_parser("test-client")
    tc.add_argument("--tool", required=True)
    tc.add_argument("--args", default="{}")
    tc.add_argument("--query")
    tc.add_argument("--repo-path")
    sub.add_parser("inspect-tools")
    sub.add_parser("show-logs")
    sub.add_parser("smoke-test")
    sub.add_parser("doctor-config")
    sub.add_parser("doctor-mcp")
    dr = sub.add_parser("doctor-rag")
    dr.add_argument("--query", default="RAG")
    return p


def main() -> None:
    args = build_parser().parse_args()
    config = load_config()
    if args.cmd == "serve":
        enabled = {"combined": None, "rag": ["rag"], "filesystem": ["filesystem"], "code": ["code"]}[args.server]
        run_stdio_server(build_registry(config, enabled))
    elif args.cmd == "legacy-serve":
        enabled = {"combined": None, "rag": ["rag"], "filesystem": ["filesystem"], "code": ["code"]}[args.server]
        run_legacy_stdio_server(build_registry(config, enabled))
    elif args.cmd == "test-client":
        registry = build_registry(config)
        payload = _loads_args(args.args)
        if args.query:
            if args.tool == "ask_knowledge_base":
                payload.setdefault("question", args.query)
            else:
                payload.setdefault("query", args.query)
        if args.repo_path:
            payload.setdefault("repo_path", args.repo_path)
        print(json.dumps(registry.call(args.tool, payload), ensure_ascii=False, indent=2))
    elif args.cmd == "inspect-tools":
        print(json.dumps({"tools": build_registry(config).list_tools()}, ensure_ascii=False, indent=2))
    elif args.cmd == "show-logs":
        log = JsonlLog(resolve_path(config, config["logging"]["tool_call_log"]))
        print(json.dumps(log.read(500), ensure_ascii=False, indent=2))
    elif args.cmd == "doctor-rag":
        registry = build_registry(config, ["rag"])
        collections = registry.call("list_collections", {})
        search = registry.call("search_documents", {"query": args.query, "top_k": 3})
        ask = registry.call("ask_knowledge_base", {"question": args.query, "top_k": 3})
        print(
            json.dumps(
                {
                    "success": bool(collections.get("success") and search.get("success") and ask.get("success")),
                    "config_path": config.get("_config_path", ""),
                    "backend": config["rag"].get("backend"),
                    "project_path": config["rag"].get("project_path") if config["rag"].get("backend") == "local_project" else None,
                    "project_config": config["rag"].get("project_config") if config["rag"].get("backend") == "local_project" else None,
                    "collections_ok": collections.get("success", False),
                    "search_ok": search.get("success", False),
                    "ask_ok": ask.get("success", False),
                    "result_count": len(search.get("data", {}).get("results", [])) if search.get("success") else 0,
                    "answer_confidence": ask.get("data", {}).get("confidence") if ask.get("success") else None,
                    "evidence_sufficient": ask.get("data", {}).get("evidence_sufficient") if ask.get("success") else None,
                    "errors": [x.get("error") for x in [collections, search, ask] if not x.get("success")],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.cmd == "doctor-mcp":
        registry = build_registry(config)
        fastmcp_installed = _module_available("mcp.server.fastmcp")
        print(
            json.dumps(
                {
                    "success": fastmcp_installed,
                    "config_path": config.get("_config_path", ""),
                    "server_name": config["mcp"]["server_name"],
                    "transport": config["mcp"].get("transport", "stdio"),
                    "fastmcp_installed": fastmcp_installed,
                    "mcp_sdk_version": _package_version("mcp") if fastmcp_installed else None,
                    "runtime_mode": "fastmcp" if fastmcp_installed else "sdk-required-not-installed",
                    "resources": ["scholarmind://collections", "scholarmind://documents/{collection}", "scholarmind://document/{doc_id}", "scholarmind://logs/recent"],
                    "prompts": ["grounded_rag_answer", "research_summary", "safe_file_organization"],
                    "tool_count": len(registry.list_tools()),
                    "tools": [t["name"] for t in registry.list_tools()],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.cmd == "doctor-config":
        print(json.dumps(doctor_config(config), ensure_ascii=False, indent=2))
    elif args.cmd == "smoke-test":
        registry = build_registry(config)
        checks = {
            "list_files": registry.call("list_files", {}),
            "search_documents": registry.call("search_documents", {"query": "RAG"}),
            "list_repo_tree": registry.call("list_repo_tree", {"repo_path": "sample_repo"}),
            "blocked_traversal": registry.call("read_file", {"path": "../secret.txt"}),
            "write_dry_run": registry.call("write_file", {"path": "notes/smoke.md", "content": "hello"}),
        }
        ok = checks["list_files"]["success"] and checks["search_documents"]["success"] and checks["list_repo_tree"]["success"] and not checks["blocked_traversal"]["success"] and checks["write_dry_run"]["success"]
        print(json.dumps({"success": ok, "checks": checks}, ensure_ascii=False, indent=2))


def _loads_args(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fixed = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', raw)
        fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
        fixed = re.sub(r':\s*([^"{\[\]\d][^,}]*)', lambda m: ': "' + m.group(1).strip() + '"', fixed)
        return json.loads(fixed)


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def doctor_config(config: dict) -> dict:
    required = ["app", "mcp", "rag", "filesystem", "code", "security", "logging"]
    errors: list[str] = []
    warnings: list[str] = []
    for key in required:
        if key not in config:
            errors.append(f"Missing required config section: {key}")
    workspace = resolve_path(config, config.get("app", {}).get("workspace_dir", "./examples/workspace"))
    data_dir = resolve_path(config, config.get("app", {}).get("data_dir", "./data"))
    log_file = resolve_path(config, config.get("logging", {}).get("tool_call_log", "./data/logs/mcp_tool_calls.jsonl"))
    if not workspace.exists():
        errors.append(f"Workspace directory does not exist: {workspace}")
    writable_dirs = {str(data_dir): _ensure_writable_dir(data_dir), str(log_file.parent): _ensure_writable_dir(log_file.parent)}
    for path, ok in writable_dirs.items():
        if not ok:
            errors.append(f"Directory is not writable: {path}")
    if config.get("rag", {}).get("backend") == "local_project":
        project_path = resolve_path(config, config.get("rag", {}).get("project_path", ""))
        if not project_path.exists():
            errors.append(f"Configured local_project RAG path does not exist: {project_path}")
        elif not (project_path / "src" / "cli.py").exists():
            warnings.append(f"local_project path exists but src/cli.py was not found: {project_path}")
        project_config = config.get("rag", {}).get("project_config")
        if project_config and not (project_path / project_config).exists():
            errors.append(f"Configured local_project project_config does not exist: {project_path / project_config}")
    for key in ["block_path_traversal", "block_symlink_escape", "block_sensitive_files", "block_hidden_dirs"]:
        if not config.get("security", {}).get(key, True):
            warnings.append(f"Security guard disabled: {key}")
    if config.get("filesystem", {}).get("allow_delete", False):
        warnings.append("filesystem.allow_delete is enabled.")
    return {
        "success": not errors,
        "config_path": config.get("_config_path", ""),
        "errors": errors,
        "warnings": warnings,
        "workspace": str(workspace),
        "writable_dirs": writable_dirs,
        "rag_backend": config.get("rag", {}).get("backend"),
        "rag_project_config": config.get("rag", {}).get("project_config"),
    }


def _ensure_writable_dir(path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
