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
            create table if not exists memories (
                memory_id text primary key,
                scope text not null,
                content text not null,
                metadata text,
                importance real not null default 0.5,
                created_at text not null,
                updated_at text not null
            );
            create index if not exists idx_memories_scope_updated on memories(scope, updated_at desc);
            create table if not exists graph_nodes (
                node_id text primary key,
                label text not null,
                node_type text not null,
                collection text,
                metadata text,
                updated_at text not null
            );
            create table if not exists graph_edges (
                source_id text not null,
                target_id text not null,
                relation text not null,
                weight real not null default 1,
                collection text,
                primary key(source_id, target_id, relation, collection)
            );
            create table if not exists graph_chunk_links (
                node_id text not null,
                chunk_id text not null,
                collection text,
                weight real not null default 1,
                primary key(node_id, chunk_id)
            );
            create index if not exists idx_graph_links_collection on graph_chunk_links(collection, node_id);
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

    def add_memory(self, memory: dict[str, Any]) -> None:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.conn.execute(
            """
            insert or replace into memories(memory_id, scope, content, metadata, importance, created_at, updated_at)
            values (:memory_id, :scope, :content, :metadata, :importance, coalesce(:created_at, :now), :now)
            """,
            {
                **memory,
                "metadata": json.dumps(memory.get("metadata", {}), ensure_ascii=False),
                "created_at": memory.get("created_at"),
                "now": now,
            },
        )
        self.conn.commit()

    def list_memories(self, scope: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "select * from memories where scope=? order by importance desc, updated_at desc limit ?",
            (scope, limit),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.get("metadata") or "{}")
            result.append(item)
        return result

    def replace_graph(self, collection: str | None, nodes: list[dict[str, Any]], edges: list[dict[str, Any]], links: list[dict[str, Any]]) -> None:
        if collection:
            self.conn.execute("delete from graph_chunk_links where collection=?", (collection,))
            self.conn.execute("delete from graph_edges where collection=?", (collection,))
            self.conn.execute("delete from graph_nodes where collection=?", (collection,))
        else:
            self.conn.execute("delete from graph_chunk_links")
            self.conn.execute("delete from graph_edges")
            self.conn.execute("delete from graph_nodes")
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.conn.executemany(
            "insert or replace into graph_nodes(node_id,label,node_type,collection,metadata,updated_at) values (:node_id,:label,:node_type,:collection,:metadata,:updated_at)",
            [{**node, "metadata": json.dumps(node.get("metadata", {}), ensure_ascii=False), "updated_at": now} for node in nodes],
        )
        self.conn.executemany(
            "insert or replace into graph_edges(source_id,target_id,relation,weight,collection) values (:source_id,:target_id,:relation,:weight,:collection)",
            edges,
        )
        self.conn.executemany(
            "insert or replace into graph_chunk_links(node_id,chunk_id,collection,weight) values (:node_id,:chunk_id,:collection,:weight)",
            links,
        )
        self.conn.commit()

    def graph_snapshot(self, collection: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        clause, params = (" where collection=?", (collection,)) if collection else ("", ())
        tables = ("graph_nodes", "graph_edges", "graph_chunk_links")
        rows = [self.conn.execute(f"select * from {table}{clause}", params).fetchall() for table in tables]
        return tuple([dict(row) for row in group] for group in rows)  # type: ignore[return-value]
