# ROADMAP

## Phase 1: Runnable Foundation

- Document ingestion
- Chunking
- Mock embedding
- Vector search
- Basic RAG QA
- Streamlit UI
- CLI
- Example data

Status: implemented for local demo.

## Phase 2: Engineered RAG

- BM25
- Hybrid search
- Reranker interface
- Citation grounding
- Confidence score
- Eval harness

Status: implemented with rule-based scoring and lightweight metrics.

## Phase 3: Agent Harness

- Tool registry
- Tool calling
- Dry-run
- Human approval
- Audit log
- Weekly report agent

Status: implemented with local tools and JSONL logs.

## Phase 4: MCP Server

- Expose `search_kb`
- Expose `ask_kb`
- Expose `list_docs`
- Expose `write_note`
- MCP client demo

Status: implemented as MCP-like JSON stdio wrapper. Official SDK transport is a future replacement.

## Phase 5: Reading RAG

- URL import
- Metadata extraction
- Topic clustering
- Reading list generation
- Notion-friendly export

Status: path and URL import, metadata extraction, keyword search, and Markdown export are implemented. Clustering is heuristic.

## Phase 6: Productization

- Complete FastAPI routes
- User accounts
- Better UI
- Docker
- CI
- Local model support
- Stronger evaluation
- Plugin system

Status: planned.

