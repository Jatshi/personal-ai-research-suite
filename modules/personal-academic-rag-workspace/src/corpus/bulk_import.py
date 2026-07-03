from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.config.config_loader import project_path
from src.corpus.classifier import classify_file, should_skip_path
from src.indexing.index_manager import IndexManager
from src.utils.file_utils import SUPPORTED_EXTENSIONS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_real_corpus(root: str | Path, output: str | Path | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    records: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if should_skip_path(path, root_path):
            continue
        file_hash = sha256_file(path)
        cls = classify_file(path, root_path)
        duplicate_of = seen.get(file_hash)
        if not duplicate_of:
            seen[file_hash] = cls["relative_path"]  # type: ignore[index]
        records.append(
            {
                "path": str(path),
                "relative_path": cls["relative_path"],
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "sha256": file_hash,
                "duplicate_of": duplicate_of,
                "collection": cls["collection"],
                "doc_type": cls["doc_type"],
                "tags": cls["tags"],
            }
        )
    manifest = {
        "root": str(root_path),
        "total_files": len(records),
        "unique_files": sum(1 for r in records if not r["duplicate_of"]),
        "duplicate_files": sum(1 for r in records if r["duplicate_of"]),
        "records": records,
    }
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def ingest_real_corpus(config: dict[str, Any], root: str | Path, manifest_output: str | Path | None = None) -> dict[str, Any]:
    manifest = scan_real_corpus(root, manifest_output)
    manager = IndexManager(config)
    existing_hashes = existing_file_hashes(manager)
    imported: list[dict[str, Any]] = []
    skipped_duplicates: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for record in manifest["records"]:
        if record["duplicate_of"] or record["sha256"] in existing_hashes:
            skipped_duplicates.append(record)
            continue
        try:
            doc_ids = manager.ingest_path(record["path"], str(record["collection"]), tags=list(record["tags"]), doc_type=str(record["doc_type"]))
            imported.append({**record, "doc_ids": doc_ids})
            existing_hashes.add(record["sha256"])
        except Exception as exc:
            failed.append({**record, "error": str(exc)})
    summary = {
        "scanned": manifest["total_files"],
        "unique": manifest["unique_files"],
        "duplicates_in_scan": manifest["duplicate_files"],
        "imported": len(imported),
        "skipped_duplicates": len(skipped_duplicates),
        "failed": len(failed),
        "imported_records": imported,
        "failed_records": failed,
    }
    out_dir = project_path(config, "./data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "real_corpus_import_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def existing_file_hashes(manager: IndexManager) -> set[str]:
    hashes: set[str] = set()
    for doc in manager.store.list_documents():
        try:
            meta = json.loads(doc.get("metadata_json") or "{}")
        except json.JSONDecodeError:
            meta = {}
        if meta.get("file_hash"):
            hashes.add(meta["file_hash"])
    return hashes


def cleanup_duplicate_documents(config: dict[str, Any]) -> dict[str, Any]:
    manager = IndexManager(config)
    keep_by_hash: dict[str, str] = {}
    deleted: list[dict[str, str]] = []
    for doc in manager.store.list_documents():
        try:
            meta = json.loads(doc.get("metadata_json") or "{}")
        except json.JSONDecodeError:
            meta = {}
        file_hash = meta.get("file_hash")
        if not file_hash:
            continue
        if file_hash in keep_by_hash:
            deleted_chunks = manager.delete_document(doc["doc_id"])
            deleted.append({"doc_id": doc["doc_id"], "duplicate_of": keep_by_hash[file_hash], "chunks": str(deleted_chunks)})
        else:
            keep_by_hash[file_hash] = doc["doc_id"]
    return {"deleted_documents": len(deleted), "deleted": deleted}


def reclassify_index_metadata(config: dict[str, Any], root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    manager = IndexManager(config)
    changed: list[dict[str, str]] = []
    with manager.store.connect() as con:
        docs = con.execute("select * from documents").fetchall()
        for doc in docs:
            metadata = json.loads(doc["metadata_json"] or "{}")
            source = metadata.get("original_source_path") or metadata.get("source_path") or doc["source_path"]
            if not source:
                continue
            source_path = Path(source)
            if not source_path.exists():
                continue
            try:
                cls = classify_file(source_path, root_path)
            except ValueError:
                continue
            new_collection = str(cls["collection"])
            new_doc_type = str(cls["doc_type"])
            new_tags = list(cls["tags"])
            old = (doc["collection"], doc["doc_type"], doc["tags"])
            new_tags_json = json.dumps(new_tags, ensure_ascii=False)
            if old == (new_collection, new_doc_type, new_tags_json):
                continue
            metadata["collection"] = new_collection
            metadata["doc_type"] = new_doc_type
            metadata["tags"] = new_tags
            con.execute(
                "update documents set collection=?, doc_type=?, tags=?, metadata_json=? where doc_id=?",
                (new_collection, new_doc_type, new_tags_json, json.dumps(metadata, ensure_ascii=False), doc["doc_id"]),
            )
            chunk_rows = con.execute("select chunk_id, metadata_json from chunks where doc_id=?", (doc["doc_id"],)).fetchall()
            for chunk in chunk_rows:
                chunk_meta = json.loads(chunk["metadata_json"] or "{}")
                chunk_meta["collection"] = new_collection
                chunk_meta["doc_type"] = new_doc_type
                chunk_meta["tags"] = new_tags
                con.execute(
                    "update chunks set collection=?, doc_type=?, tags=?, metadata_json=? where chunk_id=?",
                    (new_collection, new_doc_type, new_tags_json, json.dumps(chunk_meta, ensure_ascii=False), chunk["chunk_id"]),
                )
            changed.append({"doc_id": doc["doc_id"], "filename": doc["filename"], "collection": new_collection, "doc_type": new_doc_type})
    return {"updated_documents": len(changed), "updated": changed}
