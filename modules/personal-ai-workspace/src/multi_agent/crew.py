from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any

from src.generation.llm_client import BaseLLMClient


@dataclass(frozen=True)
class AgentRole:
    name: str
    description: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    llm_overrides: dict[str, Any] = field(default_factory=dict)

    def execute(self, task: "Task", state: dict[str, Any], llm: BaseLLMClient) -> str:
        context = [{"text": item.get("text", ""), "file_name": item.get("file_name", "")} for item in state.get("evidence", [])]
        prompt = (
            f"Role: {self.name}\n{self.system_prompt}\nTask: {task.description}\n"
            f"Shared outputs: {state.get('outputs', {})}\n"
            "Use only supplied evidence. State uncertainty explicitly."
        )
        return llm.generate(prompt, context)


@dataclass(frozen=True)
class Task:
    name: str
    description: str
    agent: AgentRole
    expected_output: str


class Crew:
    def __init__(self, tasks: list[Task], llm: BaseLLMClient | Callable[[AgentRole], BaseLLMClient]) -> None:
        self.tasks = tasks
        self.llm = llm

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        state = {**input_data, "outputs": dict(input_data.get("outputs", {})), "steps": []}
        for task in self.tasks:
            llm = self.llm(task.agent) if callable(self.llm) else self.llm
            output = task.agent.execute(task, state, llm)
            state["outputs"][task.name] = output
            state["steps"].append({"task": task.name, "agent": task.agent.name, "output": output})
        return state
