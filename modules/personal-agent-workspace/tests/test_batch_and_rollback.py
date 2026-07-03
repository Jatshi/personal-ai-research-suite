from __future__ import annotations

from pathlib import Path

from src.llm.base import BaseLLMClient
from src.tools.default_registry import build_registry
from src.tools.planner_tools import plan_agent_task, plan_agent_task_with_llm, run_agent_plan


class StaticPlannerLLM(BaseLLMClient):
    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str, context: list[dict] | None = None) -> str:
        return self.response


def test_batch_execute_dry_run_does_not_rename(cfg: dict) -> None:
    registry = build_registry(cfg)
    source = Path(cfg["app"]["workspace_dir"]) / "messy_files" / "random_report_v3.txt"
    result = registry.call(
        "execute_operations_batch",
        {"operations": [{"operation": "rename_file", "source": str(source), "new_name": "renamed.txt"}]},
        dry_run=True,
    )
    assert result.success
    assert result.output["dry_run"]
    assert source.exists()
    assert not source.with_name("renamed.txt").exists()


def test_confirmed_rename_creates_rollback_and_latest_rollback_restores(cfg: dict) -> None:
    registry = build_registry(cfg)
    source = Path(cfg["app"]["workspace_dir"]) / "messy_files" / "random_report_v3.txt"
    renamed = source.with_name("renamed.txt")
    rename = registry.call("rename_file", {"source": str(source), "new_name": "renamed.txt"}, dry_run=False, confirmed=True)
    assert rename.success
    assert renamed.exists()
    records = registry.call("list_rollback_records")
    assert records.output
    rollback = registry.call("execute_latest_rollback", dry_run=False, confirmed=True)
    assert rollback.success
    assert source.exists()


def test_rule_planner_maps_goal_to_tools(cfg: dict) -> None:
    registry = build_registry(cfg)
    plan = plan_agent_task("请扫描并整理文件 path=messy_files")
    tools = [step["tool"] for step in plan["steps"]]
    assert "organize_files" in tools
    result = run_agent_plan("请扫描并整理文件 path=messy_files", registry)
    assert result["plan"]["steps"]


def test_llm_planner_accepts_valid_json_plan(cfg: dict) -> None:
    registry = build_registry(cfg)
    llm = StaticPlannerLLM('{"goal":"scan","steps":[{"tool":"scan_folder","params":{"path":"messy_files"},"dry_run":false,"reason":"inspect files"}]}')
    plan = plan_agent_task_with_llm("扫描文件", registry, llm)
    assert plan["planner"] == "llm"
    assert plan["steps"][0]["tool"] == "scan_folder"


def test_llm_planner_falls_back_on_invalid_tool(cfg: dict) -> None:
    registry = build_registry(cfg)
    llm = StaticPlannerLLM('{"goal":"bad","steps":[{"tool":"format_disk","params":{},"dry_run":false}]}')
    plan = plan_agent_task_with_llm("完成个人 RAG 项目第一阶段", registry, llm)
    assert plan["planner"] == "rule"
    assert plan["steps"]


def test_llm_planner_forces_high_risk_dry_run(cfg: dict) -> None:
    registry = build_registry(cfg)
    llm = StaticPlannerLLM('{"goal":"rename","steps":[{"tool":"rename_file","params":{"source":"messy_files/random_report_v3.txt","new_name":"x.txt"},"dry_run":false}]}')
    plan = plan_agent_task_with_llm("重命名文件", registry, llm)
    assert plan["steps"][0]["risk"] == "high"
    assert plan["steps"][0]["dry_run"] is True
