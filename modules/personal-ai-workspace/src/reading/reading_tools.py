from __future__ import annotations

from typing import Any

from src.storage.sqlite_store import SQLiteStore
from src.utils.text_utils import tokenize


def reading_search(config: dict[str, Any], query: str, collection: str = "reading", top_k: int = 5) -> list[dict[str, Any]]:
    store = SQLiteStore(config)
    rows = store.conn.execute("select * from reading_items where collection=?", (collection,)).fetchall()
    q = set(tokenize(query))
    scored = []
    for row in rows:
        d = dict(row)
        toks = set(tokenize(d.get("title", "") + " " + d.get("summary", "") + " " + d.get("content", "")))
        d["score"] = len(q & toks) / max(len(q), 1)
        scored.append(d)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]


def reading_list_markdown(config: dict[str, Any], topic: str, output: str | None = None) -> str:
    items = reading_search(config, topic, top_k=10)
    body = [f"# 主题阅读清单：{topic}", "", "## 推荐阅读顺序"]
    for i, item in enumerate(items, start=1):
        body.append(f"{i}. {item['title']} - {item['summary'][:120]}")
    body.extend(["", "## 核心文章", *[f"- {x['title']}" for x in items[:5]], "", "## 引用来源", *[f"- {x['source_url']}" for x in items]])
    text = "\n".join(body)
    if output:
        from pathlib import Path

        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return text

