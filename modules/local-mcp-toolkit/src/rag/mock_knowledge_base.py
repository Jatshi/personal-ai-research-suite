from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from src.rag.citation import citation_from_chunk


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+", text.lower())


class MockKnowledgeBase:
    def __init__(self, collections_dir: str | Path, min_confidence: float = 0.35) -> None:
        self.collections_dir = Path(collections_dir)
        self.min_confidence = min_confidence
        self.collections_dir.mkdir(parents=True, exist_ok=True)

    def _load(self, name: str, default: Any) -> Any:
        path = self.collections_dir / name
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, name: str, value: Any) -> None:
        (self.collections_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    @property
    def collections(self) -> list[dict]:
        return self._load("collections.json", [])

    @property
    def documents(self) -> list[dict]:
        return self._load("documents.json", [])

    @property
    def chunks(self) -> list[dict]:
        return self._load("chunks.json", [])

    def search_documents(self, query: str, collection: str | None = None, top_k: int = 5, filters: dict | None = None) -> dict:
        q = Counter(_tokens(query))
        results = []
        for chunk in self.chunks:
            if collection and chunk.get("collection") != collection:
                continue
            text = f"{chunk.get('title','')} {chunk.get('text','')}"
            toks = Counter(_tokens(text))
            overlap = sum(min(q[t], toks[t]) for t in q)
            if overlap <= 0:
                continue
            score = overlap / max(len(q), 1)
            results.append(
                {
                    "doc_id": chunk["doc_id"],
                    "title": chunk.get("title", ""),
                    "file_path": chunk.get("file_path", ""),
                    "chunk_id": chunk["chunk_id"],
                    "snippet": chunk.get("text", "")[:300],
                    "score": round(score, 3),
                    "metadata": chunk.get("metadata", {}),
                }
            )
        results.sort(key=lambda r: r["score"], reverse=True)
        return {"query": query, "results": results[: max(1, min(top_k, 20))]}

    def ask_knowledge_base(self, question: str, collection: str | None = None, top_k: int = 5, require_citations: bool = True) -> dict:
        search = self.search_documents(question, collection=collection, top_k=top_k)
        if not search["results"]:
            return {"question": question, "answer": "知识库中没有足够证据回答该问题。", "confidence": 0.0, "citations": [], "evidence_sufficient": False}
        confidence = min(1.0, sum(r["score"] for r in search["results"][:3]) / 3 + 0.25)
        if confidence < self.min_confidence:
            return {"question": question, "answer": "知识库中没有足够证据回答该问题。", "confidence": round(confidence, 3), "citations": [], "evidence_sufficient": False}
        evidence = search["results"][:top_k]
        answer = "Mock KB answer: " + " ".join(r["snippet"] for r in evidence[:2])[:600]
        return {"question": question, "answer": answer, "confidence": round(confidence, 3), "citations": evidence if require_citations else [], "evidence_sufficient": True}

    def list_collections(self) -> dict:
        docs = self.documents
        chunks = self.chunks
        out = []
        for c in self.collections:
            name = c["name"]
            out.append({**c, "document_count": sum(d.get("collection") == name for d in docs), "chunk_count": sum(ch.get("collection") == name for ch in chunks)})
        return {"collections": out}

    def list_documents(self, collection: str | None = None, doc_type: str | None = None, limit: int = 50) -> dict:
        docs = []
        for doc in self.documents:
            if collection and doc.get("collection") != collection:
                continue
            if doc_type and doc.get("doc_type") != doc_type:
                continue
            docs.append(doc)
        return {"documents": docs[:limit]}

    def get_document_summary(self, doc_id: str) -> dict:
        doc = next((d for d in self.documents if d["doc_id"] == doc_id), None)
        if not doc:
            raise KeyError(f"Unknown doc_id: {doc_id}")
        chunks = [c for c in self.chunks if c.get("doc_id") == doc_id]
        summary = doc.get("summary") or " ".join(c.get("text", "") for c in chunks[:2])[:600]
        return {"doc_id": doc_id, "title": doc.get("title", ""), "summary": summary, "metadata": doc.get("metadata", {}), "citations": [citation_from_chunk(c) for c in chunks[:3]]}

    def add_document(self, file_path: str, collection: str = "default", tags: list[str] | None = None, dry_run: bool = True, confirm: bool = False) -> dict:
        path = Path(file_path)
        plan = {"operation": "add_document", "file_path": str(path), "collection": collection, "tags": tags or [], "dry_run": dry_run, "confirm": confirm}
        if dry_run:
            return {"plan": plan, "executed": False}
        if not confirm:
            raise PermissionError("confirm=true required")
        docs = self.documents
        chunks = self.chunks
        doc_id = f"doc_{len(docs)+1}"
        text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        doc = {"doc_id": doc_id, "title": path.stem, "file_path": str(path), "collection": collection, "doc_type": path.suffix.lstrip("."), "created_at": "", "updated_at": "", "summary": text[:300], "metadata": {"tags": tags or []}}
        docs.append(doc)
        chunks.append({"doc_id": doc_id, "title": path.stem, "file_path": str(path), "chunk_id": f"{doc_id}_chunk_1", "collection": collection, "text": text, "metadata": {"tags": tags or []}})
        self._save("documents.json", docs)
        self._save("chunks.json", chunks)
        return {"plan": plan, "executed": True, "doc_id": doc_id}

    def delete_document(self, doc_id: str, dry_run: bool = True, confirm: bool = False) -> dict:
        plan = {"operation": "delete_document", "doc_id": doc_id, "dry_run": dry_run, "confirm": confirm}
        if dry_run:
            return {"plan": plan, "executed": False}
        if not confirm:
            raise PermissionError("confirm=true required")
        docs = [d for d in self.documents if d.get("doc_id") != doc_id]
        chunks = [c for c in self.chunks if c.get("doc_id") != doc_id]
        self._save("documents.json", docs)
        self._save("chunks.json", chunks)
        return {"plan": plan, "executed": True}

