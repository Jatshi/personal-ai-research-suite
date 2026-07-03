from __future__ import annotations

import re
from pathlib import Path

from src.safety.path_guard import PathGuard


def read_todo(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    tasks = []
    for line in text.splitlines():
        match = re.match(r"- \[( |x|X)\]\s*(.+)", line.strip())
        if not match:
            continue
        body = match.group(2)
        deadline = re.search(r"deadline[:=]([0-9-]+)", body, re.I)
        priority = re.search(r"priority[:=](high|medium|low)", body, re.I)
        tasks.append(
            {
                "done": match.group(1).lower() == "x",
                "text": body,
                "deadline": deadline.group(1) if deadline else "",
                "priority": priority.group(1).lower() if priority else "medium",
            }
        )
    return {"path": path, "tasks": tasks, "completed": [t for t in tasks if t["done"]], "open": [t for t in tasks if not t["done"]]}


def write_todo(path: str, task: str, guard: PathGuard, dry_run: bool = True, confirmed: bool = False) -> dict:
    p = guard.validate(path, for_write=True)
    line = f"- [ ] {task}\n"
    if dry_run:
        return {"path": str(p), "append": line, "dry_run": True}
    if not confirmed:
        raise PermissionError("write_todo requires confirmation")
    with p.open("a", encoding="utf-8") as f:
        f.write(line)
    return {"path": str(p), "append": line, "executed": True}


def generate_daily_report(todo_path: str) -> str:
    data = read_todo(todo_path)
    done = "\n".join(f"- {t['text']}" for t in data["completed"]) or "- None"
    open_tasks = "\n".join(f"- {t['text']}" for t in data["open"]) or "- None"
    high_priority = [t for t in data["open"] if t["priority"] == "high"]
    risks = "\n".join(f"- High priority pending: {t['text']}" for t in high_priority) or "- No high-priority pending tasks found."
    return f"# Daily Report\n\n## 今日完成\n{done}\n\n## 遇到的问题\n- 请结合实际工作记录补充阻塞项。\n\n## 明日计划\n{open_tasks}\n\n## 风险提醒\n{risks}\n"


def generate_weekly_report(todo_path: str) -> str:
    data = read_todo(todo_path)
    done = "\n".join(f"- {t['text']}" for t in data["completed"]) or "- None"
    open_tasks = "\n".join(f"- {t['text']}" for t in data["open"]) or "- None"
    return (
        "# Weekly Report\n\n"
        f"## 本周完成\n{done}\n\n"
        "## 关键进展\n"
        f"- Completed tasks: {len(data['completed'])}\n"
        f"- Open tasks: {len(data['open'])}\n\n"
        "## 问题与风险\n"
        "- 未完成任务需要按 priority 和 deadline 重新排序。\n\n"
        f"## 下周计划\n{open_tasks}\n"
    )


def generate_email_draft(recipient: str, goal: str, key_points: str, tone: str = "professional") -> str:
    return (
        f"Subject: {goal}\n\n"
        f"Dear {recipient},\n\n"
        f"I am writing to {goal}.\n\n"
        f"Key points:\n{key_points}\n\n"
        f"Tone: {tone}.\n\n"
        "Best regards,"
    )
