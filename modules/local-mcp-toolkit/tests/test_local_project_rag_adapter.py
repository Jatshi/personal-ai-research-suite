from __future__ import annotations

from pathlib import Path

from src.rag.adapters import LocalCliRagAdapter


def test_local_cli_rag_adapter_parses_json_cli(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "cli.py").write_text(
        """
from __future__ import annotations
import argparse, json
import os

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("search")
s.add_argument("--query")
s.add_argument("--mode")
s.add_argument("--top-k")
a = sub.add_parser("ask")
a.add_argument("--query")
a.add_argument("--top-k")
sub.add_parser("list-docs")
d = sub.add_parser("show-doc")
d.add_argument("--doc-id")
i = sub.add_parser("ingest")
i.add_argument("--path")
i.add_argument("--collection")
delete = sub.add_parser("delete-doc")
delete.add_argument("--doc-id")
delete.add_argument("--confirm", action="store_true")
ns = p.parse_args()
if ns.cmd == "search":
    print(json.dumps({"config": os.getenv("PERSONAL_AI_CONFIG", ""), "results": [{"doc_id": "d1", "file_name": "paper.md", "chunk_id": "c1", "text": "RAG evidence", "score": 0.9}]}))
elif ns.cmd == "ask":
    print(json.dumps({"success": True, "answer": "RAG answer", "confidence": 0.8, "citations": ["[1] paper.md"], "evidence": [{"doc_id": "d1", "file_name": "paper.md", "chunk_id": "c1", "text": "RAG evidence", "score": 0.9}]}))
elif ns.cmd == "list-docs":
    print(json.dumps({"documents": [{"doc_id": "d1", "file_name": "paper.md"}]}))
elif ns.cmd == "show-doc":
    print(json.dumps({"document": {"doc_id": ns.doc_id, "title": "Paper"}}))
elif ns.cmd == "ingest":
    print(json.dumps({"success": True, "documents": [{"doc_id": "d2", "file_path": ns.path, "collection": ns.collection}]}))
else:
    print(json.dumps({"success": True, "executed": ns.confirm, "deleted": ns.doc_id}))
""",
        encoding="utf-8",
    )
    adapter = LocalCliRagAdapter(tmp_path, min_confidence=0.35, project_config="config.production.yaml")
    search = adapter.search_documents("RAG", top_k=3)
    assert search["results"][0]["chunk_id"] == "c1"
    answer = adapter.ask_knowledge_base("RAG?")
    assert answer["evidence_sufficient"]
    assert answer["citations"]
    dry = adapter.add_document("paper.md", "personal", dry_run=True)
    assert not dry["executed"]
    added = adapter.add_document("paper.md", "personal", dry_run=False, confirm=True)
    assert added["executed"]
    deleted = adapter.delete_document("d2", dry_run=False, confirm=True)
    assert deleted["executed"]
