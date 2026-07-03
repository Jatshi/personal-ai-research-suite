from __future__ import annotations

from collections import Counter
from typing import Any

from src.utils.text_utils import keyword_summary


def cluster_topics(items: list[dict[str, Any]], max_topics: int = 5) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(keyword_summary(item.get("title", "") + " " + item.get("summary", ""), 5))
    topics = []
    for topic, _ in counter.most_common(max_topics):
        members = [i for i in items if topic.lower() in (i.get("title", "") + " " + i.get("summary", "")).lower()]
        topics.append({"topic": topic, "items": members})
    return topics

