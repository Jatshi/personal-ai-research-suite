from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from src.ingestion.document_loader import load_document
from src.ingestion.url_loader import load_url
from src.storage.sqlite_store import SQLiteStore
from src.utils.hash_utils import sha256_text
from src.utils.text_utils import first_sentences, keyword_summary


def import_reading_path(config: dict[str, Any], path: str, collection: str = "reading") -> list[dict[str, Any]]:
    root = Path(path)
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt", ".html", ".htm", ".pdf"}]
    items = []
    store = SQLiteStore(config)
    for file in files:
        loaded = load_document(file)
        item = _reading_item(loaded["text"], loaded["metadata"], collection, str(file))
        store.conn.execute(
            "insert or replace into reading_items values (:item_id,:title,:author,:publish_date,:source_url,:site_name,:collection,:summary,:content,:metadata)",
            item,
        )
        store.conn.commit()
        items.append(item)
    return items


def import_reading_url(config: dict[str, Any], url: str, collection: str = "reading") -> dict[str, Any]:
    loaded = load_url(url)
    item = _reading_item(loaded["text"], loaded["metadata"], collection, url)
    store = SQLiteStore(config)
    store.conn.execute(
        "insert or replace into reading_items values (:item_id,:title,:author,:publish_date,:source_url,:site_name,:collection,:summary,:content,:metadata)",
        item,
    )
    store.conn.commit()
    return item


def _reading_item(text: str, meta: dict[str, Any], collection: str, source: str) -> dict[str, Any]:
    item_id = sha256_text(f"{collection}:{source}")[:16]
    return {
        "item_id": item_id,
        "title": meta.get("title") or Path(source).stem,
        "author": meta.get("author", ""),
        "publish_date": meta.get("publish_date", ""),
        "source_url": meta.get("source_url", source),
        "site_name": meta.get("site_name", ""),
        "collection": collection,
        "summary": first_sentences(text, 260),
        "content": text,
        "metadata": '{"tags": %r, "imported_at": "%s"}' % (keyword_summary(text, 6), time.strftime("%Y-%m-%dT%H:%M:%S")),
    }

