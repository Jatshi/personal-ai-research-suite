from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class WorkspaceSQLiteStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def init_db(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                create table if not exists file_inventory (
                    path text primary key,
                    filename text,
                    extension text,
                    size integer,
                    modified_time text,
                    hash text,
                    is_duplicate integer,
                    is_temp integer,
                    is_empty_or_abnormal integer,
                    category text,
                    summary text,
                    metadata_json text,
                    updated_at text
                );
                create index if not exists idx_file_inventory_hash on file_inventory(hash);
                create index if not exists idx_file_inventory_extension on file_inventory(extension);
                create index if not exists idx_file_inventory_category on file_inventory(category);
                """
            )

    def upsert_files(self, files: list[dict[str, Any]]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as con:
            con.executemany(
                """
                insert into file_inventory values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(path) do update set
                    filename=excluded.filename,
                    extension=excluded.extension,
                    size=excluded.size,
                    modified_time=excluded.modified_time,
                    hash=excluded.hash,
                    is_duplicate=excluded.is_duplicate,
                    is_temp=excluded.is_temp,
                    is_empty_or_abnormal=excluded.is_empty_or_abnormal,
                    category=excluded.category,
                    summary=excluded.summary,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                [
                    (
                        f.get("path"),
                        f.get("filename"),
                        f.get("extension"),
                        f.get("size"),
                        f.get("modified_time"),
                        f.get("hash"),
                        int(bool(f.get("is_duplicate"))),
                        int(bool(f.get("is_temp"))),
                        int(bool(f.get("is_empty_or_abnormal"))),
                        f.get("category"),
                        f.get("summary"),
                        json.dumps(f, ensure_ascii=False),
                        now,
                    )
                    for f in files
                    if f.get("path")
                ],
            )

    def list_files(self, limit: int = 500, category: str | None = None) -> list[dict[str, Any]]:
        sql = "select * from file_inventory"
        params: list[Any] = []
        if category:
            sql += " where category=?"
            params.append(category)
        sql += " order by updated_at desc limit ?"
        params.append(limit)
        with self.connect() as con:
            rows = con.execute(sql, params).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            except json.JSONDecodeError:
                item["metadata"] = {}
            return_bool_keys = ("is_duplicate", "is_temp", "is_empty_or_abnormal")
            for key in return_bool_keys:
                item[key] = bool(item[key])
            out.append(item)
        return out
