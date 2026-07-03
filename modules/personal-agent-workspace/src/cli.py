from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.agents.file_organizer_agent import FileOrganizerAgent
from src.agents.paper_reading_workflow import PaperReadingWorkflow
from src.agents.thesis_finishing_agent import ThesisFinishingAgent
from src.agents.work_assistant_agent import WorkAssistantAgent
from src.config.config_loader import load_config, resolve_project_path
from src.safety.audit_log import JsonlAuditLog
from src.tools.default_registry import build_registry
from src.llm.providers import build_llm_client
from src.tools.planner_tools import run_agent_plan


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("personal-agent-workspace")
    sub = p.add_subparsers(dest="cmd", required=True)
    scan = sub.add_parser("scan-files")
    scan.add_argument("--path", required=True)
    org = sub.add_parser("organize-files")
    org.add_argument("--path", required=True)
    org.add_argument("--dry-run", action="store_true")
    batch = sub.add_parser("execute-organize-plan")
    batch.add_argument("--path", required=True)
    batch.add_argument("--execute", action="store_true")
    batch.add_argument("--yes", action="store_true")
    thesis = sub.add_parser("check-thesis")
    thesis.add_argument("--path", required=True)
    papers = sub.add_parser("read-papers")
    papers.add_argument("--path", required=True)
    papers.add_argument("--output", required=True)
    assistant = sub.add_parser("assistant")
    assistant.add_argument("--goal", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--execute", action="store_true")
    plan.add_argument("--yes", action="store_true")
    plan.add_argument("--llm-planner", action="store_true")
    daily = sub.add_parser("daily-report")
    daily.add_argument("--todo", required=True)
    weekly = sub.add_parser("weekly-report")
    weekly.add_argument("--todo", required=True)
    email = sub.add_parser("email-draft")
    email.add_argument("--recipient", required=True)
    email.add_argument("--goal", required=True)
    email.add_argument("--key-points", required=True)
    sub.add_parser("file-inventory")
    sub.add_parser("show-rollback")
    rollback = sub.add_parser("rollback-latest")
    rollback.add_argument("--execute", action="store_true")
    rollback.add_argument("--yes", action="store_true")
    sub.add_parser("show-logs")
    return p


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args()
    config = load_config()
    registry = build_registry(config)
    if args.cmd == "scan-files":
        result = FileOrganizerAgent(registry).scan(args.path)
        _print_json(result)
    elif args.cmd == "organize-files":
        result = FileOrganizerAgent(registry).organize(args.path)
        _print_json(result)
    elif args.cmd == "execute-organize-plan":
        plan = FileOrganizerAgent(registry).organize(args.path)
        dry_run = not args.execute
        confirmed = bool(args.execute and args.yes)
        result = registry.call("execute_operations_batch", {"operations": plan["dry_run_operations"]}, dry_run=dry_run, confirmed=confirmed)
        _print_json(result.__dict__)
    elif args.cmd == "check-thesis":
        result = ThesisFinishingAgent(registry).check(args.path)
        print("Generated thesis reports:")
        print(resolve_project_path(config, config["app"]["data_dir"]) / "exports" / "thesis_check_report.md")
        print(resolve_project_path(config, config["app"]["data_dir"]) / "exports" / "thesis_check_report.json")
        _print_json({"todo_count": len(result["todos"])})
    elif args.cmd == "read-papers":
        result = PaperReadingWorkflow(registry).run(args.path, args.output)
        print(f"Generated notes in {result['output_dir']}")
        print(f"Processed {len(result['papers'])} papers")
    elif args.cmd == "assistant":
        print(WorkAssistantAgent(registry).assistant(args.goal))
    elif args.cmd == "plan":
        llm = build_llm_client(config) if args.llm_planner else None
        result = run_agent_plan(args.goal, registry, execute=args.execute, confirmed=args.yes, llm=llm, use_llm=args.llm_planner)
        _print_json(result)
    elif args.cmd == "daily-report":
        print(WorkAssistantAgent(registry).daily_report(args.todo))
    elif args.cmd == "weekly-report":
        print(WorkAssistantAgent(registry).weekly_report(args.todo))
    elif args.cmd == "email-draft":
        result = registry.call("generate_email_draft", {"recipient": args.recipient, "goal": args.goal, "key_points": args.key_points})
        print(result.output)
    elif args.cmd == "file-inventory":
        result = registry.call("list_file_inventory")
        _print_json(result.output)
    elif args.cmd == "show-rollback":
        result = registry.call("list_rollback_records")
        _print_json(result.output)
    elif args.cmd == "rollback-latest":
        dry_run = not args.execute
        confirmed = bool(args.execute and args.yes)
        result = registry.call("execute_latest_rollback", dry_run=dry_run, confirmed=confirmed)
        _print_json(result.__dict__)
    elif args.cmd == "show-logs":
        log = JsonlAuditLog(resolve_project_path(config, config["logging"]["tool_log_file"]))
        _print_json(log.read())


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
