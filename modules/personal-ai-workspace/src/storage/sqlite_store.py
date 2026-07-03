from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from src.config.config_loader import resolve_project_path


class SQLiteStore:
    def __init__(self, config: dict[str, Any]):
        data_dir = config.get("app", {}).get("data_dir", "./data")
        db_dir = resolve_project_path(config, data_dir) / "sqlite"
        db_dir.mkdir(parents=True, exist_ok=True)
        self.path = db_dir / "workspace.db"
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            create table if not exists documents (
                doc_id text primary key,
                file_name text,
                file_path text,
                file_type text,
                collection text,
                title text,
                author text,
                source_type text,
                language text,
                tags text,
                metadata text,
                imported_at text
            );
            create table if not exists chunks (
                chunk_id text primary key,
                doc_id text,
                collection text,
                file_name text,
                section_title text,
                page_number integer,
                paragraph_number integer,
                text text,
                embedding text,
                metadata text
            );
            create table if not exists notes (
                note_id text primary key,
                title text,
                path text,
                content text,
                created_at text
            );
            create table if not exists reading_items (
                item_id text primary key,
                title text,
                author text,
                publish_date text,
                source_url text,
                site_name text,
                collection text,
                summary text,
                content text,
                metadata text
            );
            """
        )
        self.conn.commit()

    def upsert_document(self, doc: dict[str, Any]) -> None:
        self.conn.execute(
            """
            insert or replace into documents values
            (:doc_id,:file_name,:file_path,:file_type,:collection,:title,:author,:source_type,:language,:tags,:metadata,:imported_at)
            """,
            {
                **doc,
                "tags": json.dumps(doc.get("tags", []), ensure_ascii=False),
                "metadata": json.dumps(doc.get("metadata", {}), ensure_ascii=False),
                "imported_at": doc.get("imported_at") or time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        self.conn.commit()

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        doc_ids = {chunk.get("doc_id") for chunk in chunks if chunk.get("doc_id")}
        for doc_id in doc_ids:
            self.conn.execute("delete from chunks where doc_id=?", (doc_id,))
        for chunk in chunks:
            self.conn.execute(
                """
                insert or replace into chunks values
                (:chunk_id,:doc_id,:collection,:file_name,:section_title,:page_number,:paragraph_number,:text,:embedding,:metadata)
                """,
                {
                    **chunk,
                    "embedding": json.dumps(chunk.get("embedding", [])),
                    "metadata": json.dumps(chunk.get("metadata", {}), ensure_ascii=False),
                },
            )
        self.conn.commit()

    def list_documents(self, collection: str | None = None) -> list[dict[str, Any]]:
        if collection:
            rows = self.conn.execute("select * from documents where collection=? order by imported_at desc", (collection,)).fetchall()
        else:
            rows = self.conn.execute("select * from documents order by imported_at desc").fetchall()
        return [dict(r) for r in rows]

    def get_chunks(self, collection: str | None = None) -> list[dict[str, Any]]:
        if collection:
            rows = self.conn.execute("select * from chunks where collection=?", (collection,)).fetchall()
        else:
            rows = self.conn.execute("select * from chunks").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["embedding"] = json.loads(d.get("embedding") or "[]")
            d["metadata"] = json.loads(d.get("metadata") or "{}")
            out.append(d)
        return out

    def delete_document(self, doc_id: str) -> None:
        self.conn.execute("delete from chunks where doc_id=?", (doc_id,))
        self.conn.execute("delete from documents where doc_id=?", (doc_id,))
        self.conn.commit()

    def delete_collection(self, collection: str) -> None:
        self.conn.execute("delete from chunks where collection=?", (collection,))
        self.conn.execute("delete from documents where collection=?", (collection,))
        self.conn.commit()

    def count_documents(self) -> int:
        return int(self.conn.execute("select count(*) from documents").fetchone()[0])
