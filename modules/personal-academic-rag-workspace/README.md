# personal-academic-rag-workspace

`personal-academic-rag-workspace` is a local-first personal and academic RAG system for papers, thesis notes, project materials, resumes, meeting notes, and literature reading workflows.

It runs offline in mock mode by default and can switch to real OpenAI or OpenAI-compatible LLM and embedding APIs by setting environment variables and using `config.production.yaml`.

## Features

- Ingest PDF, Word `docx`, PowerPoint `pptx`, Markdown, and TXT files.
- Parse documents into source-aware segments and chunks.
- Store document, chunk, paper metadata, and search logs in SQLite.
- Index chunks in Chroma when available, with JSON cosine fallback.
- Retrieve with BM25 keyword search, semantic vector search, or hybrid search.
- Rerank results with a rule-based reranker.
- Generate grounded answers with citations and confidence scores.
- Refuse unsupported questions with `知识库中没有足够证据回答该问题。`
- Provide Academic RAG utilities: paper metadata extraction, section parsing, reading notes, comparison, and literature tables.
- Provide CLI, Streamlit UI, example data, tests, and an evaluation harness.

## Does RAG Need Training?

Usually, no. A standard RAG pipeline is:

```text
documents -> parse -> chunk -> embed -> index -> retrieve -> rerank -> build context -> LLM answer with citations
```

Training is optional. You may later fine-tune embeddings, train a cross-encoder reranker, or fine-tune an LLM for style, but the first production baseline should be retrieval, reranking, grounding, citations, and evaluation.

## Tech Stack

- Python 3.11+
- Streamlit
- SQLite metadata store
- Chroma vector store with JSON fallback
- Built-in BM25 keyword retrieval
- OpenAI / OpenAI-compatible LLM and embedding clients
- Mock LLM and mock embedding fallback
- pytest

## Install

```powershell
cd D:\博士毕业论文\personal-academic-rag-workspace
pip install -r requirements.txt
```

## Quick Start In Mock Mode

No API key is required.

```powershell
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_papers --collection academic
python -m src.cli search --query "RAG 是什么？" --mode hybrid --top-k 5
python -m src.cli ask --query "请总结示例论文的方法。" --collection academic
streamlit run app/streamlit_app.py
```

Mock mode verifies the full engineering chain. Answer quality is intentionally limited because the LLM and embeddings are deterministic local mocks.

## Use A Real LLM API

Set the production config and your API key:

```powershell
$env:PERSONAL_ACADEMIC_RAG_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
```

For OpenAI-compatible gateways, set:

```powershell
$env:OPENAI_BASE_URL="http://localhost:11434/v1"
```

Or copy `.env.example` to `.env` and fill in the values. Do not commit real API keys.

`config.production.yaml` uses:

```yaml
embedding:
  backend: openai
  model_name: text-embedding-3-small

llm:
  backend: openai
  model_name: gpt-4o-mini
```

Run diagnostics:

```powershell
python -m src.cli doctor-config
python -m src.cli doctor-llm
python -m src.cli doctor-llm --call-api
```

`doctor-config` checks config sections, writable workspace paths, Chroma availability, and required API key environment variables. `doctor-llm` checks provider construction. `--call-api` makes a real chat and embedding call.

After switching embedding models, rebuild the index. Mock embeddings use 384 dimensions; `text-embedding-3-small` uses 1536 dimensions.

```powershell
$env:PERSONAL_ACADEMIC_RAG_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_papers --collection academic
python -m src.cli ask --query "请总结示例论文的方法。" --collection academic
```

One-command production check:

```powershell
.\run_production_check.ps1 -CallApi
```

## CLI

```powershell
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_papers --collection academic
python -m src.cli search --query "我的博士研究创新点是什么？" --mode hybrid --top-k 5
python -m src.cli ask --query "请总结这些材料中关于复杂声学场景的内容" --collection academic
python -m src.cli reindex --collection academic
python -m src.cli delete --doc-id <doc_id>
python -m src.cli export-notes --collection academic --output ./data/exports/notes.md
python -m src.cli eval --dataset ./examples/eval/rag_eval.jsonl --output ./data/exports/rag_eval_report.md
python -m src.cli scan-real-corpus --root "D:\博士毕业论文"
python -m src.cli ingest-real-corpus --root "D:\博士毕业论文"
python -m src.cli cleanup-duplicates
python -m src.cli reclassify-corpus --root "D:\博士毕业论文"
python -m src.cli doctor-config
python -m src.cli doctor-llm --call-api
```

## Streamlit UI

```powershell
streamlit run app/streamlit_app.py
```

Pages:

- Documents: upload, import, list, delete, and reindex documents.
- Search: keyword, semantic, and hybrid search with scores and snippets.
- Ask: grounded QA with confidence and citations.
- Academic: paper metadata, notes, comparison, and literature tables.
- Settings: view and edit configuration.

## Evaluation

```powershell
python -m src.cli eval --dataset ./examples/eval/rag_eval.jsonl --output ./data/exports/rag_eval_report.md
```

Metrics include retrieval hit rate, citation presence, evidence sufficiency accuracy, refusal accuracy, and average confidence.

## Project Structure

```text
app/                 Streamlit UI
src/ingestion/       file parsers and batch ingestion
src/chunking/        chunking and metadata construction
src/indexing/        Chroma/fallback vector store, BM25, index manager
src/retrieval/       keyword, semantic, hybrid retrieval and reranker
src/generation/      LLM/embedding clients, mock clients, OpenAI-compatible clients
src/grounding/       citations, confidence, evidence checker
src/academic/        paper metadata, section parser, notes, comparison, table
src/storage/         SQLite metadata and file registry
src/evaluation.py    RAG evaluation harness
examples/            synthetic demo data
tests/               pytest coverage
```

## Production-Ready vs Demo-Grade

Implemented:

- Real OpenAI-compatible LLM and embedding clients.
- Env-based API key configuration and `.env` loading.
- Production config file and diagnostics.
- Chroma-first vector persistence with JSON fallback.
- SQLite metadata and search logging.
- BM25, semantic, hybrid retrieval, and rule reranking.
- Grounded citations, confidence scoring, and refusal behavior.
- CLI, UI, tests, example data, and evaluation harness.

Still demo-grade:

- PDF layout understanding is text-extraction based, not layout-aware.
- Reranker is rule-based, not a trained cross-encoder.
- Access control is local-only, not multi-user auth.
- Evaluation dataset is small and should be expanded for publishable claims.
- No background job queue for very large document batches.

## Tests

```powershell
.\run_tests.ps1
```

or:

```powershell
pytest -q
```

## Roadmap

- Add SentenceTransformers embedding backend.
- Add Ollama-specific examples.
- Add cross-encoder reranker backend.
- Add larger RAG evaluation datasets.
- Add file watcher for incremental indexing.
- Add Docker and GitHub Actions CI.
- Add stronger PDF section, table, and reference extraction.

## Resume Description

Designed and implemented `personal-academic-rag-workspace`, a local-first academic RAG system for personal knowledge management and paper reading. The system supports multi-format document ingestion, SQLite metadata, Chroma vector indexing, BM25 keyword retrieval, hybrid search, rule-based reranking, OpenAI-compatible LLM/embedding backends, grounded citations, evidence-based refusal, confidence scoring, Streamlit UI, CLI tools, Academic RAG note generation, and pytest-based validation.
