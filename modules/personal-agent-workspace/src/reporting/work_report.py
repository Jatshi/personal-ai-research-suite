from __future__ import annotations


def generate_task_breakdown(goal: str) -> str:
    return f"""# Task Breakdown

Goal: {goal}

| Task | Priority | Difficulty | Dependency | Suggested Order |
|---|---|---|---|---:|
| Clarify deliverables and acceptance commands | high | low | none | 1 |
| Implement minimum runnable workflow | high | medium | deliverables | 2 |
| Add tests and examples | high | medium | implementation | 3 |
| Write README and usage notes | medium | low | tests/examples | 4 |
| Review logs and risks | medium | low | all previous | 5 |
"""

