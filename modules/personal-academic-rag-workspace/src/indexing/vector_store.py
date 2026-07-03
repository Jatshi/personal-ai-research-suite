from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.generation.llm_client import BaseEmbeddingClient
from src.models import Chunk, SearchResult
from src.utils.text_utils import cosine


class VectorStore:
    def __init__(self, persist_dir: str | Path, embedding_client: BaseEmbeddingClient, collection_name: str = "rag_chunks") -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_client = embedding_client
        self.collection_name = collection_name
        self.backend = "json"
        self._client = None
        self._collection = None
        safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in collection_name)
        self.index_file = self.persist_dir / f"{safe_name}_fallback.json"
        if not self.index_file.exists():
            self.index_file.write_text("[]", encoding="utf-8")
        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.persist_dir / "chroma"))
            self._collection = self._client.get_or_create_collection(collection_name)
            self.backend = "chroma"
        except Exception:
            self.backend = "json"

    def upsert(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        embeddings = self.embedding_client.embed_texts([c.text for c in chunks])
        if self.backend == "chroma":
            assert self._collection is not None
            self._collection.upsert(
                ids=[c.chunk_id for c in chunks],
                documents=[c.text for c in chunks],
                metadatas=[self._flat_metadata(c.metadata) for c in chunks],
                embeddings=embeddings,
            )
            self._upsert_json_rows(chunks, embeddings)
            return
        self._upsert_json_rows(chunks, embeddings)

    def _upsert_json_rows(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        rows = self._load_rows()
        rows_by_id = {r["chunk_id"]: r for r in rows}
        for c, emb in zip(chunks, embeddings):
            rows_by_id[c.chunk_id] = {"chunk_id": c.chunk_id, "doc_id": c.doc_id, "text": c.text, "metadata": c.metadata, "embedding": emb}
        self._save_rows(list(rows_by_id.values()))

    def search(self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[SearchResult]:
        qemb = self.embedding_client.embed_query(query)
        filters = filters or {}
        if self.backend == "chroma":
            assert self._collection is not None
            where = {k: v for k, v in filters.items() if k in {"collection", "doc_type"} and v}
            try:
                res = self._collection.query(query_embeddings=[qemb], n_results=top_k, where=where or None)
                out: list[SearchResult] = []
                ids = res.get("ids", [[]])[0]
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                distances = res.get("distances", [[]])[0] if res.get("distances") else [0.0] * len(ids)
                for cid, doc, meta, dist in zip(ids, docs, metas, distances):
                    chunk = Chunk(chunk_id=cid, doc_id=str(meta.get("doc_id", "")), text=doc, metadata=dict(meta))
                    score = max(0.0, 1.0 - float(dist))
                    out.append(SearchResult(chunk=chunk, score=score, vector_score=score))
                return out
            except Exception:
                pass
        rows = self._load_rows()
        out = []
        for r in rows:
            meta = r["metadata"]
            if filters.get("collection") and meta.get("collection") != filters["collection"]:
                continue
            if filters.get("doc_type") and meta.get("doc_type") != filters["doc_type"]:
                continue
            score = cosine(qemb, r["embedding"])
            out.append(SearchResult(chunk=Chunk(r["chunk_id"], r["doc_id"], r["text"], meta), score=score, vector_score=score))
        return sorted(out, key=lambda x: x.score, reverse=True)[:top_k]

    def delete_chunks(self, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return
        if self.backend == "chroma":
            assert self._collection is not None
            try:
                self._collection.delete(ids=chunk_ids)
            except Exception:
                pass
        rows = [r for r in self._load_rows() if r["chunk_id"] not in set(chunk_ids)]
        self._save_rows(rows)

    @staticmethod
    def _flat_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        out = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[k] = "" if v is None else v
            else:
                out[k] = json.dumps(v, ensure_ascii=False)
        return out

    def _load_rows(self) -> list[dict[str, Any]]:
        return json.loads(self.index_file.read_text(encoding="utf-8"))

    def _save_rows(self, rows: list[dict[str, Any]]) -> None:
        self.index_file.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
