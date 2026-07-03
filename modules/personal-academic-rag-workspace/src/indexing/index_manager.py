from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from src.academic.paper_metadata_extractor import PaperMetadataExtractor
from src.academic.section_parser import SectionParser
from src.chunking.chunker import TextChunker
from src.config.config_loader import project_path
from src.generation.answer_generator import AnswerGenerator
from src.generation.providers import build_embedding_client, build_llm_client
from src.indexing.bm25_store import BM25Store
from src.indexing.vector_store import VectorStore
from src.ingestion.document_loader import load_document
from src.models import Answer, Chunk, SearchResult
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.keyword_retriever import KeywordRetriever
from src.retrieval.semantic_retriever import SemanticRetriever
from src.storage.file_registry import FileRegistry
from src.storage.metadata_store import MetadataStore
from src.utils.file_utils import iter_supported_files


class IndexManager:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.project_root = Path(config["_project_root"])
        workspace = project_path(config, config["app"]["workspace_dir"])
        self.raw_dir = workspace / "raw"
        self.store = MetadataStore(workspace / "metadata" / "rag.sqlite")
        self.file_registry = FileRegistry(self.project_root, self.raw_dir)
        self.embedding = build_embedding_client(config)
        self.llm = build_llm_client(config)
        self.vector_store = VectorStore(workspace / "indexes", self.embedding, collection_name=self._vector_collection_name())
        self.chunker = TextChunker(config["chunking"]["chunk_size"], config["chunking"]["chunk_overlap"])

    def _vector_collection_name(self) -> str:
        embedding_config = self.config.get("embedding", {})
        raw = f"rag_chunks_{embedding_config.get('backend', 'mock')}_{embedding_config.get('model_name', 'model')}"
        return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in raw)[:63]

    def ingest_path(self, path: str | Path, collection: str, tags: list[str] | None = None, doc_type: str = "general") -> list[str]:
        source = Path(path).resolve()
        doc_ids: list[str] = []
        for file_path in iter_supported_files(source):
            file_hash = self._sha256_file(file_path)
            stored = self.file_registry.register(file_path, collection)
            segments = load_document(stored, collection=collection, tags=tags, doc_type=doc_type)
            for segment in segments:
                segment.metadata["original_source_path"] = str(file_path)
                segment.metadata["file_hash"] = file_hash
            chunks = self.chunker.chunk(segments)
            if not chunks:
                continue
            doc_id = chunks[0].doc_id
            self.store.upsert_document(doc_id, chunks[0].metadata, str(stored))
            self.store.upsert_chunks(chunks)
            self.vector_store.upsert(chunks)
            if collection == "academic" or doc_type == "paper":
                self._save_paper(chunks)
            doc_ids.append(doc_id)
        return doc_ids

    def _save_paper(self, chunks: list[Chunk]) -> None:
        sections = SectionParser().parse(chunks)
        meta = PaperMetadataExtractor().extract(chunks)
        self.store.save_paper(chunks[0].doc_id, meta, sections)
        self.store.upsert_chunks(chunks)

    def build_retriever(self) -> HybridRetriever:
        chunks = self.store.list_chunks()
        bm25 = BM25Store(chunks)
        return HybridRetriever(
            KeywordRetriever(bm25),
            SemanticRetriever(self.vector_store),
            self.config["retrieval"]["bm25_weight"],
            self.config["retrieval"]["vector_weight"],
        )

    def search(self, query: str, mode: str | None = None, top_k: int | None = None, filters: dict | None = None) -> list[SearchResult]:
        mode = mode or self.config["retrieval"]["default_mode"]
        top_k = top_k or self.config["retrieval"]["top_k"]
        results = self.build_retriever().search(query, top_k=top_k, mode=mode, filters=filters)
        self.store.log_search(
            query,
            mode,
            top_k,
            [{"chunk_id": r.chunk.chunk_id, "score": r.score, "rerank_score": r.rerank_score} for r in results],
        )
        return results

    def ask(self, query: str, collection: str | None = None, mode: str | None = None, top_k: int | None = None) -> Answer:
        filters = {"collection": collection} if collection else {}
        results = self.search(query, mode=mode, top_k=top_k, filters=filters)
        answer = AnswerGenerator(self.llm, self.config["retrieval"]["min_confidence"]).answer(query, results)
        self.store.log_search(
            query,
            mode or self.config["retrieval"]["default_mode"],
            top_k or self.config["retrieval"]["top_k"],
            [{"chunk_id": r.chunk.chunk_id, "score": r.score, "rerank_score": r.rerank_score} for r in results],
            answer.confidence,
        )
        return answer

    def reindex(self, collection: str | None = None) -> int:
        chunks = self.store.list_chunks({"collection": collection} if collection else {})
        self.vector_store.upsert(chunks)
        return len(chunks)

    def delete_document(self, doc_id: str) -> int:
        chunk_ids = self.store.delete_document(doc_id)
        self.vector_store.delete_chunks(chunk_ids)
        return len(chunk_ids)

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
