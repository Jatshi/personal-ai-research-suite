from __future__ import annotations

from typing import Any


def generate_weekly_report(tasks: list[dict[str, Any]], evidence: list[dict[str, Any]] | None = None, start: str = "", end: str = "") -> str:
    done = [t for t in tasks if t.get("done")]
    todo = [t for t in tasks if not t.get("done")]
    sources = evidence or []
    return f"""# 周报

## 一、本周完成事项
{_items([t['text'] for t in done])}

## 二、关键进展
{_items([s.get('file_name', s.get('title', 'source')) + ': ' + (s.get('text', s.get('snippet', ''))[:120]) for s in sources[:3]])}

## 三、问题与风险
{_items([t['text'] for t in todo if t.get('priority', '').lower() in {'high', 'p0', 'p1'}])}

## 四、下周计划
{_items([t['text'] for t in todo])}

## 五、需要协同或确认的事项
- 需要用户补充未记录在 todo/notes 中的外部进展。

## 六、引用来源
{_items([s.get('file_name', s.get('title', 'source')) for s in sources[:5]])}
"""


def generate_daily_report(tasks: list[dict[str, Any]], evidence: list[dict[str, Any]] | None = None, date: str = "") -> str:
    done = [t for t in tasks if t.get("done")]
    todo = [t for t in tasks if not t.get("done")]
    return f"""# 日报

## 今日完成
{_items([t['text'] for t in done])}

## 进行中
{_items([t['text'] for t in todo[:5]])}

## 问题与风险
- 证据不足的部分需要继续补充原始记录。

## 明日计划
{_items([t['text'] for t in todo[:5]])}

## 引用来源
{_items([s.get('file_name', s.get('title', 'source')) for s in (evidence or [])[:5]])}
"""


def _items(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items if x) or "- 暂无可用证据。"

