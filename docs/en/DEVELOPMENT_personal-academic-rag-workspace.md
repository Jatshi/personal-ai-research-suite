# Development: personal-academic-rag-workspace

## Architecture

```text
ingestion -> chunking -> indexing -> retrieval -> reranking -> grounding -> generation
```

## Key Modules

- `src/ingestion/`: PDF, docx, pptx, Markdown, and TXT parsing.
- `src/chunking/`: source-aware chunking with page, paragraph, and heading metadata.
- `src/indexing/`: Chroma/JSON vector store and BM25 keyword index.
- `src/retrieval/`: keyword, semantic, and hybrid retrievers.
- `src/retrieval/reranker.py`: rule-based reranker.
- `src/grounding/`: citation builder, confidence score, evidence checker.
- `src/generation/`: LLM/embedding interfaces, mock clients, OpenAI-compatible clients.
- `src/academic/`: paper metadata, section parsing, paper notes, literature tables.

## Why RAG Usually Does Not Need Training

The baseline RAG pipeline is:

1. Parse documents.
2. Split into chunks.
3. Generate embeddings.
4. Store vectors.
5. Retrieve with BM25 and vector search.
6. Rerank results.
7. Build evidence context.
8. Ask the LLM to answer from evidence.
9. Validate citations and confidence.

## Production Readiness

- Real API mode uses `config.production.yaml`.
- Secrets are read from environment variables.
- `doctor-config` validates config, directories, dependencies, and keys.
- `doctor-llm --call-api` verifies real LLM and embedding endpoints.
- Chroma is preferred for production; JSON fallback keeps demos runnable.
- Reindex after changing embedding models.

## Interview Talking Points

- Why hybrid search is more robust than vector-only retrieval.
- Why retrieval and reranking should be separate stages.
- How citation grounding reduces hallucination.
- How the system detects insufficient evidence.
- Why mock backends are important for deterministic tests.
- How to add SentenceTransformers, Ollama, or a cross-encoder reranker.

## Roadmap

- Local embedding backend.
- Cross-encoder reranker.
- Better PDF layout parsing.
- Larger RAG evaluation dataset.
