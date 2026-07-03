from __future__ import annotations

from functools import partial
from pathlib import Path

from src.config.config_loader import resolve_project_path
from src.llm.providers import build_llm_client
from src.reporting.work_report import generate_task_breakdown
from src.safety.audit_log import JsonlAuditLog
from src.safety.path_guard import PathGuard
from src.safety.rollback import RollbackStore
from src.storage.sqlite_store import WorkspaceSQLiteStore
from src.tools.file_tools import (
    build_file_organization_plan,
    delete_file,
    execute_latest_rollback,
    execute_operations_batch,
    find_duplicates,
    move_file,
    rename_file,
    scan_folder,
)
from src.tools.paper_tools import run_paper_reading_workflow
from src.tools.planner_tools import plan_agent_task_with_llm
from src.tools.rag_tools import search_knowledge_base
from src.tools.thesis_tools import run_thesis_check
from src.tools.todo_tools import generate_daily_report, generate_email_draft, generate_weekly_report, read_todo, write_todo
from src.tools.tool_registry import ToolRegistry, ToolSpec


def build_registry(config: dict) -> ToolRegistry:
    project_root = Path(config["_project_root"])
    workspace = resolve_project_path(config, config["app"]["workspace_dir"])
    data_dir = resolve_project_path(config, config["app"]["data_dir"])
    tool_log = JsonlAuditLog(resolve_project_path(config, config["logging"]["tool_log_file"]))
    audit = JsonlAuditLog(resolve_project_path(config, config["logging"]["audit_log_file"]))
    rollback = RollbackStore(data_dir / "logs" / "rollback.jsonl")
    store = WorkspaceSQLiteStore(data_dir / "indexes" / "agent_workspace.sqlite")
    guard = PathGuard(
        workspace,
        block_hidden=config["safety"]["block_hidden_files"],
        block_env=config["safety"]["block_env_files"],
        allow_outside=config["safety"]["allow_paths_outside_workspace"],
    )
    registry = ToolRegistry(tool_log)
    allowed = config["file_organizer"]["allowed_extensions"]
    llm = build_llm_client(config)
    exports = data_dir / "exports"

    def read_path(path: str) -> str:
        p = Path(path)
        if p.is_absolute() and p.exists():
            return str(p)
        candidate = project_root / path
        if candidate.exists():
            return str(candidate.resolve())
        return str(guard.validate(path, must_exist=True))

    def read_guard(path: str) -> PathGuard:
        resolved = Path(read_path(path)).resolve()
        examples_root = (project_root / "examples").resolve()
        if resolved == examples_root or examples_root in resolved.parents:
            return PathGuard(examples_root, allow_outside=True)
        return guard

    def spec(name: str, description: str, required: list[str], risk: str = "low", confirm: bool = False) -> ToolSpec:
        return ToolSpec(name, description, {"type": "object", "required": required}, risk, confirm)

    registry.register(spec("scan_folder", "Scan workspace folder", ["path"]), lambda path: scan_folder(read_path(path), allowed, read_guard(path), store))
    registry.register(spec("find_duplicates", "Find duplicates", ["path"]), lambda path: find_duplicates(read_path(path), allowed, read_guard(path), store))
    registry.register(spec("organize_files", "Build dry-run organization plan", ["path"], "medium", False), lambda path, dry_run=True: build_file_organization_plan(read_path(path), allowed, read_guard(path), llm, store))
    registry.register(spec("list_file_inventory", "List indexed files", []), lambda: store.list_files())
    registry.register(spec("move_file", "Move a file", ["source", "target"], "high", True), lambda source, target, dry_run=True, confirmed=False: move_file(source, target, guard, audit, rollback, dry_run, confirmed))
    registry.register(spec("rename_file", "Rename a file", ["source", "new_name"], "high", True), lambda source, new_name, dry_run=True, confirmed=False: rename_file(source, new_name, guard, audit, rollback, dry_run, confirmed))
    registry.register(spec("delete_file", "Delete a file", ["path"], "high", True), lambda path, dry_run=True, confirmed=False: delete_file(path, guard, audit, dry_run, confirmed, config["safety"]["allow_delete"]))
    registry.register(spec("execute_operations_batch", "Execute a batch of planned file operations", ["operations"], "high", True), lambda operations, dry_run=True, confirmed=False: execute_operations_batch(operations, guard, audit, rollback, dry_run, confirmed, config["safety"]["allow_delete"]))
    registry.register(spec("list_rollback_records", "List rollback records", []), lambda: rollback.read())
    registry.register(spec("execute_latest_rollback", "Execute the latest rollback record", [], "high", True), lambda dry_run=True, confirmed=False: execute_latest_rollback(guard, audit, rollback, dry_run, confirmed))
    registry.register(spec("check_thesis", "Run thesis checks", ["path"]), lambda path: run_thesis_check(read_path(path), exports))
    registry.register(spec("read_papers", "Run multi-agent paper workflow", ["path", "output"]), lambda path, output: run_paper_reading_workflow(read_path(path), resolve_project_path(config, output)))
    registry.register(spec("read_todo", "Read todo", ["path"]), lambda path: read_todo(read_path(path)))
    registry.register(spec("write_todo", "Write todo", ["path", "task"], "high", True), lambda path, task, dry_run=True, confirmed=False: write_todo(path, task, guard, dry_run, confirmed))
    registry.register(spec("generate_todo_list", "Generate task breakdown", ["goal"]), generate_task_breakdown)
    registry.register(spec("generate_daily_report", "Generate daily report", ["todo_path"]), lambda todo_path: generate_daily_report(read_path(todo_path)))
    registry.register(spec("generate_weekly_report", "Generate weekly report", ["todo_path"]), lambda todo_path: generate_weekly_report(read_path(todo_path)))
    registry.register(spec("generate_email_draft", "Generate email draft", ["recipient", "goal", "key_points"]), generate_email_draft)
    rag_root = resolve_project_path(config, config.get("rag", {}).get("project_dir", "../personal-academic-rag-workspace"))
    registry.register(spec("search_knowledge_base", "Mock or adapter RAG search", ["query"]), lambda query: search_knowledge_base(query, str(rag_root)))
    registry.register(spec("plan_agent_task", "Plan an agent task from natural language", ["goal"]), lambda goal: plan_agent_task_with_llm(goal, registry, llm))
    return registry
