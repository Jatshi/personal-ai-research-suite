from __future__ import annotations

from src.rag.mock_knowledge_base import MockKnowledgeBase
from src.safety.path_guard import PathGuard


class RagTools:
    def __init__(self, kb: MockKnowledgeBase, guard: PathGuard, audit_log) -> None:
        self.kb = kb
        self.guard = guard
        self.audit_log = audit_log

    def search_documents(self, query: str, collection: str | None = None, top_k: int = 5, filters: dict | None = None) -> dict:
        return self.kb.search_documents(query, collection, top_k, filters)

    def ask_knowledge_base(self, question: str, collection: str | None = None, top_k: int = 5, require_citations: bool = True) -> dict:
        return self.kb.ask_knowledge_base(question, collection, top_k, require_citations)

    def list_collections(self) -> dict:
        return self.kb.list_collections()

    def list_documents(self, collection: str | None = None, doc_type: str | None = None, limit: int = 50) -> dict:
        return self.kb.list_documents(collection, doc_type, limit)

    def get_document_summary(self, doc_id: str) -> dict:
        return self.kb.get_document_summary(doc_id)

    def add_document(self, file_path: str, collection: str = "default", tags: list[str] | None = None, dry_run: bool = True, confirm: bool = False) -> dict:
        path = self.guard.validate(file_path, must_exist=True)
        result = self.kb.add_document(str(path), collection, tags, dry_run, confirm)
        if result.get("executed"):
            self.audit_log.append({"operation": "add_document", "file_path": str(path), "collection": collection, "doc_id": result.get("doc_id")})
        return result

    def delete_document(self, doc_id: str, dry_run: bool = True, confirm: bool = False) -> dict:
        result = self.kb.delete_document(doc_id, dry_run, confirm)
        if result.get("executed"):
            self.audit_log.append({"operation": "delete_document", "doc_id": doc_id})
        return result

