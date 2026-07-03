from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.rag.mock_knowledge_base import MockKnowledgeBase


def get_knowledge_base(config: dict) -> MockKnowledgeBase:
    from src.config.config_loader import resolve_path

    if config["rag"].get("backend") == "local_project":
        return LocalCliRagAdapter(
            resolve_path(config, config["rag"]["project_path"]),
            config["rag"].get("min_confidence", 0.35),
            project_config=config["rag"].get("project_config"),
        )
    return MockKnowledgeBase(resolve_path(config, config["rag"]["collections_dir"]), config["rag"].get("min_confidence", 0.35))


class LocalCliRagAdapter(MockKnowledgeBase):
    """Adapter for local RAG projects with compatible JSON CLI commands."""

    def __init__(self, project_path: Path, min_confidence: float = 0.35, project_config: str | None = None) -> None:
        self.project_path = project_path
        self.min_confidence = min_confidence
        self.project_config = project_config

    def search_documents(self, query: str, collection: str | None = None, top_k: int = 5, filters: dict | None = None) -> dict:
        cmd = [sys.executable, "-m", "src.cli", "search", "--query", query, "--mode", "hybrid", "--top-k", str(top_k)]
        if collection:
            cmd += ["--collection", collection]
        payload = self._run_json(cmd)
        results = payload.get("results", []) if isinstance(payload, dict) else []
        return {"query": query, "results": [self._normalize_result(r) for r in results[:top_k]]}

    def ask_knowledge_base(self, question: str, collection: str | None = None, top_k: int = 5, require_citations: bool = True) -> dict:
        cmd = [sys.executable, "-m", "src.cli", "ask", "--query", question, "--top-k", str(top_k)]
        if collection:
            cmd += ["--collection", collection]
        payload = self._run_json(cmd)
        if not isinstance(payload, dict):
            text = str(payload)
            sufficient = "知识库中没有足够证据" not in text and "not enough evidence" not in text.lower()
            return {"question": question, "answer": text, "confidence": 0.7 if sufficient else 0.0, "citations": [], "evidence_sufficient": sufficient}
        answer = payload.get("answer", "")
        confidence = float(payload.get("confidence", 0.0) or 0.0)
        evidence = payload.get("evidence", [])
        sufficient = bool(payload.get("success", True)) and confidence >= self.min_confidence and "知识库中没有足够证据" not in answer
        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "citations": payload.get("citations", []) if require_citations else [],
            "evidence": [self._normalize_result(r) for r in evidence[:top_k]],
            "evidence_sufficient": sufficient,
            "adapter": "local_project",
            "project_path": str(self.project_path),
            "project_config": self.project_config,
        }

    def list_collections(self) -> dict:
        return {"collections": [{"name": "local_project", "backend": "cli", "project_path": str(self.project_path), "project_config": self.project_config}]}

    def list_documents(self, collection: str | None = None, doc_type: str | None = None, limit: int = 50) -> dict:
        cmd = [sys.executable, "-m", "src.cli", "list-docs"]
        if collection:
            cmd += ["--collection", collection]
        payload = self._run_json(cmd)
        docs = payload.get("documents", []) if isinstance(payload, dict) else []
        if doc_type:
            docs = [d for d in docs if d.get("doc_type") == doc_type or d.get("file_type") == doc_type]
        return {"documents": docs[:limit]}

    def get_document_summary(self, doc_id: str) -> dict:
        cmd = [sys.executable, "-m", "src.cli", "show-doc", "--doc-id", doc_id]
        payload = self._run_json(cmd)
        doc = payload.get("document", {}) if isinstance(payload, dict) else {}
        return {"doc_id": doc_id, "title": doc.get("title", ""), "summary": str(doc.get("metadata", ""))[:1000], "metadata": doc}

    def add_document(self, file_path: str, collection: str = "default", tags: list[str] | None = None, dry_run: bool = True, confirm: bool = False) -> dict:
        plan = {
            "operation": "local_project_ingest",
            "file_path": file_path,
            "collection": collection,
            "tags": tags or [],
            "dry_run": dry_run,
            "confirm": confirm,
            "project_path": str(self.project_path),
            "project_config": self.project_config,
        }
        if dry_run:
            return {"plan": plan, "executed": False}
        if not confirm:
            raise PermissionError("confirm=true required")
        cmd = [sys.executable, "-m", "src.cli", "ingest", "--path", file_path, "--collection", collection]
        payload = self._run_json(cmd)
        return {"plan": plan, "executed": True, "result": payload}

    def delete_document(self, doc_id: str, dry_run: bool = True, confirm: bool = False) -> dict:
        plan = {
            "operation": "local_project_delete_doc",
            "doc_id": doc_id,
            "dry_run": dry_run,
            "confirm": confirm,
            "project_path": str(self.project_path),
            "project_config": self.project_config,
        }
        if dry_run:
            return {"plan": plan, "executed": False}
        if not confirm:
            raise PermissionError("confirm=true required")
        payload = self._run_json([sys.executable, "-m", "src.cli", "delete-doc", "--doc-id", doc_id, "--confirm"])
        return {"plan": plan, "executed": True, "result": payload}

    def _run_json(self, cmd: list[str]) -> Any:
        env = os.environ.copy()
        if self.project_config:
            env["PERSONAL_AI_CONFIG"] = self.project_config
        proc = subprocess.run(cmd, cwd=self.project_path, text=True, capture_output=True, timeout=90, encoding="utf-8", errors="replace", env=env)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-1500:] or proc.stdout[-1500:])
        text = proc.stdout.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    @staticmethod
    def _normalize_result(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "doc_id": item.get("doc_id", ""),
            "title": item.get("title") or item.get("file_name", ""),
            "file_path": item.get("file_path", ""),
            "chunk_id": item.get("chunk_id", ""),
            "snippet": item.get("snippet") or item.get("text", "")[:300],
            "score": item.get("score", item.get("confidence", 0.0)),
            "metadata": item.get("metadata", {}),
            "file_name": item.get("file_name", ""),
            "page_number": item.get("page_number"),
            "paragraph_number": item.get("paragraph_number"),
        }
