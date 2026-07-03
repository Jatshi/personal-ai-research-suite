from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.models import Chunk


class MetadataStore:
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
                create table if not exists documents (
                    doc_id text primary key,
                    filename text,
                    source_path text,
                    stored_path text,
                    file_type text,
                    collection text,
                    tags text,
                    date text,
                    imported_at text,
                    modified_at text,
                    doc_type text,
                    metadata_json text
                );
                create table if not exists chunks (
                    chunk_id text primary key,
                    doc_id text,
                    text text,
                    collection text,
                    filename text,
                    page text,
                    paragraph text,
                    doc_type text,
                    tags text,
                    metadata_json text
                );
                create table if not exists papers (
                    doc_id text primary key,
                    metadata_json text,
                    sections_json text
                );
                create table if not exists search_logs (
                    id integer primary key autoincrement,
                    created_at datetime default current_timestamp,
                    query text,
                    mode text,
                    top_k integer,
                    results_json text,
                    confidence real
                );
                """
            )

    def upsert_document(self, doc_id: str, metadata: dict[str, Any], stored_path: str) -> None:
        with self.connect() as con:
            con.execute(
                """
                insert or replace into documents values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    metadata.get("filename"),
                    metadata.get("source_path"),
                    stored_path,
                    metadata.get("file_type"),
                    metadata.get("collection"),
                    json.dumps(metadata.get("tags", []), ensure_ascii=False),
                    metadata.get("date"),
                    metadata.get("imported_at"),
                    metadata.get("modified_at"),
                    metadata.get("doc_type"),
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        with self.connect() as con:
            con.executemany(
                """
                insert or replace into chunks values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.chunk_id,
                        c.doc_id,
                        c.text,
                        c.metadata.get("collection"),
                        c.metadata.get("filename"),
                        str(c.metadata.get("page") or ""),
                        str(c.metadata.get("paragraph") or ""),
                        c.metadata.get("doc_type"),
                        json.dumps(c.metadata.get("tags", []), ensure_ascii=False),
                        json.dumps(c.metadata, ensure_ascii=False),
                    )
                    for c in chunks
                ],
            )

    def list_documents(self, collection: str | None = None) -> list[dict[str, Any]]:
        sql = "select * from documents"
        params: tuple[Any, ...] = ()
        if collection:
            sql += " where collection=?"
            params = (collection,)
        sql += " order by imported_at desc"
        with self.connect() as con:
            return [dict(r) for r in con.execute(sql, params).fetchall()]

    def list_chunks(self, filters: dict[str, Any] | None = None) -> list[Chunk]:
        filters = filters or {}
        clauses: list[str] = []
        params: list[Any] = []
        for key in ("collection", "doc_type"):
            if filters.get(key):
                clauses.append(f"{key}=?")
                params.append(filters[key])
        if filters.get("folder"):
            clauses.append("json_extract(metadata_json, '$.source_path') like ?")
            params.append(f"%{filters['folder']}%")
        sql = "select * from chunks"
        if clauses:
            sql += " where " + " and ".join(clauses)
        with self.connect() as con:
            rows = con.execute(sql, params).fetchall()
        chunks: list[Chunk] = []
        for r in rows:
            meta = json.loads(r["metadata_json"])
            chunks.append(Chunk(chunk_id=r["chunk_id"], doc_id=r["doc_id"], text=r["text"], metadata=meta))
        if filters.get("tags"):
            wanted = set(filters["tags"])
            chunks = [c for c in chunks if wanted & set(c.metadata.get("tags", []))]
        return chunks

    def get_chunks_by_doc(self, doc_id: str) -> list[Chunk]:
        with self.connect() as con:
            rows = con.execute("select * from chunks where doc_id=?", (doc_id,)).fetchall()
        return [Chunk(chunk_id=r["chunk_id"], doc_id=r["doc_id"], text=r["text"], metadata=json.loads(r["metadata_json"])) for r in rows]

    def delete_document(self, doc_id: str) -> list[str]:
        chunks = self.get_chunks_by_doc(doc_id)
        with self.connect() as con:
            con.execute("delete from chunks where doc_id=?", (doc_id,))
            con.execute("delete from documents where doc_id=?", (doc_id,))
            con.execute("delete from papers where doc_id=?", (doc_id,))
        return [c.chunk_id for c in chunks]

    def save_paper(self, doc_id: str, metadata: dict[str, Any], sections: dict[str, str]) -> None:
        with self.connect() as con:
            con.execute(
                "insert or replace into papers values (?, ?, ?)",
                (doc_id, json.dumps(metadata, ensure_ascii=False), json.dumps(sections, ensure_ascii=False)),
            )

    def list_papers(self) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("select * from papers").fetchall()
        out = []
        for r in rows:
            meta = json.loads(r["metadata_json"])
            meta["doc_id"] = r["doc_id"]
            meta["sections"] = json.loads(r["sections_json"])
            out.append(meta)
        return out

    def log_search(self, query: str, mode: str, top_k: int, results: list[dict[str, Any]], confidence: float = 0.0) -> None:
        with self.connect() as con:
            con.execute(
                "insert into search_logs(query, mode, top_k, results_json, confidence) values (?, ?, ?, ?, ?)",
                (query, mode, top_k, json.dumps(results, ensure_ascii=False), confidence),
            )

