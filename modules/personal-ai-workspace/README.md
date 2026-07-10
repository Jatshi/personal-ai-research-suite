# personal-ai-workspace

`personal-ai-workspace` is a local-first Personal AI OS. It combines a document knowledge base, RAG question answering, Agent tool calling, MCP-like tools, evaluation harness, daily/weekly report generation, reading collection management, observability, and safety controls.

It runs offline in mock mode for reproducible tests, and can switch to real OpenAI-compatible LLM and embedding APIs through `config.yaml` plus `.env`.

## Why This Is A Personal AI Workspace

This project is not a single chatbot. It is a small AI operating layer around personal materials:

- Knowledge base: ingest and search local documents.
- RAG: answer with citations and refuse when evidence is insufficient.
- Agent Harness: call tools with state, dry-run, confirmation, and logs.
- LLM Tool Planner: use the configured LLM to propose safe JSON tool plans, with mock fallback for offline tests.
- MCP-like Server: expose local abilities as structured tools.
- Evaluation: measure retrieval, citation, refusal, and confidence behavior.
- Reports: generate Chinese daily and weekly reports from todo and evidence.
- Reading RAG: import articles and create topic reading lists.
- Observability: JSONL logs for RAG, tools, audits, LLM calls, and errors.

## Tech Stack

- Python
- Streamlit UI
- Optional FastAPI API
- SQLite metadata store
- Built-in BM25 and vector search
- Optional Chroma persistent vector store
- Mock and OpenAI-compatible LLM clients
- Mock and OpenAI-compatible embedding clients
- MCP-like JSON stdio server
- pytest

SQLite stores metadata and chunks. The default lightweight vector backend stores embeddings in SQLite for offline tests; production mode can use Chroma for persistent semantic retrieval. Reindex after changing embedding models.

## Install

```bash
cd D:\博士毕业论文\personal-ai-workspace
pip install -r requirements.txt
```

Editable install with console script:

```bash
pip install -e ".[dev]"
personal-ai-workspace --help
```

This repository is packaged as a source application. The console script is intended for editable/source checkouts and loads `src/cli.py` from the repository root to avoid top-level `src` package collisions with other local projects.

## Real LLM / Embedding API Mode

The project supports real OpenAI-compatible chat and embedding APIs while keeping mock mode as the offline default.

1. Copy the environment template:

```bash
copy .env.example .env
```

2. Fill `.env`:

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

For OpenAI-compatible providers, change `OPENAI_BASE_URL` to the provider endpoint.

3. Edit `config.yaml`:

```yaml
app:
  mock_mode: false

llm:
  backend: openai
  model_name: gpt-4.1-mini
  api_key_env: OPENAI_API_KEY
  base_url_env: OPENAI_BASE_URL

embedding:
  backend: openai
  model_name: text-embedding-3-small
  api_key_env: OPENAI_API_KEY
  base_url_env: OPENAI_BASE_URL
```

For deployment, you can also copy the production template:

```bash
copy config.production.yaml config.yaml
```

Or keep the default config untouched and select the production config per process:

```powershell
$env:PERSONAL_AI_CONFIG="config.production.yaml"
python -m src.cli doctor-llm
.\run_api.ps1
```

4. Check configuration without spending tokens:

```bash
python -m src.cli doctor-llm
```

Validate the whole config before starting services:

```bash
python -m src.cli doctor-config
```

5. Optionally send a minimal real API request:

```bash
python -m src.cli doctor-llm --call-api
```

Or run the production check script:

```powershell
$env:PERSONAL_AI_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
.\run_production_check.ps1 -CallApi
```

Without a real key, use `-AllowMissingSecrets` to verify local production wiring without making paid API calls:

```powershell
.\run_production_check.ps1 -AllowMissingSecrets
```

6. Re-ingest documents after changing embedding models:

```bash
python -m src.cli ingest --path ./examples/sample_docs --collection personal
```

Embeddings are stored with chunks in SQLite. If you switch from mock embeddings to a real embedding model, re-ingest or reindex documents so query embeddings and stored chunk embeddings use the same vector space.

For production Chroma vector storage, install:

```bash
pip install -r requirements-production.txt
```

Then use `config.production.yaml` or set:

```yaml
vector_store:
  backend: chroma
  persist_dir: ./data/indexes/chroma
```

SQLite remains the metadata store. Chroma is used for semantic retrieval when enabled, while SQLite continues to support BM25, filters, citations, UI lists, and auditability.

## Quick Start

```bash
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_notes --collection notes
python -m src.cli search --query "RAG 是什么？" --mode hybrid --top-k 5
python -m src.cli ask --query "请总结这个知识库中的主要主题。" --collection personal
```

## Streamlit

```bash
streamlit run app/streamlit_app.py
```

On Windows PowerShell:

```powershell
.\run_streamlit.ps1
```

Pages: Dashboard, Knowledge Base, Search and Ask, Agent Workspace, Daily/Weekly Report, Reading RAG, Evaluation, MCP Tools, Observability, Settings.

## FastAPI

```bash
uvicorn src.api.fastapi_app:app --host 127.0.0.1 --port 8000
```

On Windows PowerShell:

```powershell
.\run_api.ps1
```

Implemented endpoints:

- `GET /health`
- `POST /rag/search`
- `POST /rag/ask`
- `POST /agent/run`
- `POST /kb/ingest`
- `GET /kb/docs`
- `POST /kb/reindex`
- `POST /kb/delete`
- `GET /llm/doctor`
- `GET /observability/logs`

Request bodies are validated with Pydantic models. Additional routes can be added over the same registry and storage layers without changing the CLI or Streamlit implementation.

### API Token Protection

API authentication is disabled by default for local use. To protect FastAPI endpoints in a shared environment:

```yaml
server:
  api_auth_enabled: true
  api_token_env: PERSONAL_AI_API_TOKEN
```

Set the token in `.env`:

```bash
PERSONAL_AI_API_TOKEN=change-this-before-deploying
```

Then call protected endpoints with either:

```bash
curl -H "Authorization: Bearer $PERSONAL_AI_API_TOKEN" http://127.0.0.1:8000/llm/doctor
curl -H "X-API-Key: $PERSONAL_AI_API_TOKEN" http://127.0.0.1:8000/llm/doctor
```

`GET /health` remains public for container health checks.

## Docker

```bash
copy .env.example .env
docker compose up --build api
docker compose up --build streamlit
```

The API listens on `http://127.0.0.1:8000`; Streamlit listens on `http://127.0.0.1:8501`. The compose file mounts `./data` for persistence and `./examples` read-only for sample data.

For production API-backed Chroma mode:

```bash
copy .env.example .env
docker compose -f docker-compose.production.yml up --build api
docker compose -f docker-compose.production.yml up --build streamlit
```

The production compose file installs `requirements-production.txt` and mounts `config.production.yaml` as `/app/config.yaml`.

## CLI

```bash
python -m src.cli --help
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli list-docs --collection personal
python -m src.cli reindex --collection personal
python -m src.cli search --query "RAG 是什么？" --mode hybrid --top-k 5
python -m src.cli ask --query "请总结这个知识库中的主要主题。" --collection personal
python -m src.cli agent --goal "根据本周笔记和 todo 生成周报"
python -m src.cli daily-report --date 2026-07-02 --collection notes
python -m src.cli weekly-report --from 2026-07-01 --to 2026-07-07 --collection notes
python -m src.cli import-reading --path ./examples/sample_reading --collection reading
python -m src.cli reading-search --query "哪些文章讲了 Agent Harness？"
python -m src.cli reading-list --topic "AI Agent 安全" --output ./data/exports/reading/agent_safety.md
python -m src.cli eval-rag --dataset ./examples/sample_eval/rag_eval.jsonl
python -m src.cli eval-agent --dataset ./examples/sample_eval/agent_eval.jsonl
python -m src.cli mcp-client --tool search_kb --args "{\"query\":\"RAG 是什么？\"}"
python -m src.cli show-logs
```

## RAG Design

For a deeper system overview, see `ARCHITECTURE.md`.

The RAG pipeline is:

```text
load document -> chunk -> metadata -> configured embedding -> SQLite metadata/chunks + optional Chroma vectors -> BM25/vector/hybrid search -> evidence check -> configured LLM answer -> citations
```

If evidence confidence is too low, the system returns:

```text
知识库中没有足够证据回答该问题。
```

## Phase 6 Advanced RAG

The default remains grounded hybrid retrieval. Advanced controls are opt-in in
`config.yaml`: query rewriting (`hyde` or `decomposition`), context compression,
CRAG routing, and bounded multi-hop retrieval. Low CRAG confidence always follows
the evidence-insufficient refusal path.

```powershell
python -m src.cli search --query "Compare RAG retrieval and agent safety" --crag --multi-hop
python -m src.cli ask --query "Explain RAG from the evidence" --query-rewrite hyde
```

Search and ask responses expose `retrieval_trace`, including query variants,
route decision, hop history, and compression statistics.

## Phase 6 GraphRAG And Research Crew

Build the SQLite-backed graph index and query it directly or alongside hybrid
retrieval:

```powershell
python -m src.cli mcp-client --tool ingest --args '{"path":"examples/sample_docs","collection":"personal"}'
curl -X POST http://127.0.0.1:8000/graph/build -H "Content-Type: application/json" -d '{"collection":"personal"}'
```

Use `retrieval.backend: graphrag` or `hybrid+graphrag` after a graph build. The
five-role research crew is available through `POST /agents/crew/run`; it records
Reader, Method, Experiment, Critic, and Writer outputs in `multi_agent_runs.jsonl`.

## Evaluation

```powershell
python -m src.cli eval-ab --dataset ./examples/sample_eval/phase6_rag_eval.jsonl --config-a '{"retrieval":{"top_k":2}}' --config-b '{"retrieval":{"top_k":5}}'
python -m src.cli eval-rag --engine ragas --dataset ./examples/sample_eval/phase6_rag_eval.jsonl
```

The first command is offline-capable. RAGAS requires the production extra and a
configured OpenAI-compatible chat and embedding API.

## Next.js Workbench

The product UI is in `../../apps/web` and runs alongside Streamlit:

```powershell
cd ../../apps/web
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

It provides Dashboard, Import, Search, Agent, File Organizer, Thesis Check, Paper
Reading, Observability, MCP, and Settings routes. RAG and Agent screens consume
FastAPI SSE endpoints; all other routes remain compatible with existing Streamlit
workflows during migration.

## Agent Harness

Tools are registered with `ToolSpec`:

```python
ToolSpec(
    name="write_note",
    description="Write markdown note",
    input_schema={"path": "str", "content": "str"},
    risk_level="high",
    requires_confirmation=True,
    category="notes",
)
```

High-risk write tools default to dry-run and require confirmation before execution.

The personal assistant agent can use the configured LLM as a tool planner. It sends the current goal and available tool schemas to the LLM, expects a JSON plan, validates tool names and arguments locally, forces high-risk write tools into dry-run mode unless explicitly confirmed, and then executes through the same `ToolRegistry`.

Offline mode uses `MockLLMClient`, which returns a deterministic JSON plan. Production mode uses `OpenAICompatibleLLMClient` when `llm.backend: openai`.

Set `agent.execution_mode: react` or run `python -m src.cli agent --goal "..." --mode react`
to use native OpenAI-compatible function calling. ReAct keeps all write operations
behind the existing dry-run and confirmation policy and can use opt-in SQLite
long-term memory via `agent.enable_long_term_memory`.

## MCP-like Server

```bash
python -m src.cli mcp-serve
```

The server accepts JSON lines:

```json
{"method":"tools/list"}
{"method":"tools/call","tool":"search_kb","arguments":{"query":"RAG 是什么？"}}
```

This JSON-stdio wrapper uses the same tool registry as CLI/API/UI. If you need the official MCP SDK transport, keep the registry and replace only the transport wrapper.

## Evaluation Harness

```bash
python -m src.cli eval-rag --dataset ./examples/sample_eval/rag_eval.jsonl --output ./data/exports/eval/rag_eval_report.md
```

Metrics include retrieval hit rate, source accuracy, citation presence, refusal accuracy, keyword coverage, and average confidence.

Agent evaluation is also implemented:

```bash
python -m src.cli eval-agent --dataset ./examples/sample_eval/agent_eval.jsonl --output ./data/exports/eval/agent_eval_report.md
```

It checks agent success, expected tool coverage, and confirmation-policy behavior.

## Reading RAG

```bash
python -m src.cli import-reading --path ./examples/sample_reading --collection reading
python -m src.cli reading-search --query "Agent Harness"
python -m src.cli reading-list --topic "AI Agent 安全"
```

The first version uses rule-based metadata extraction and keyword similarity. URL import is available through `import-url`.

## Safety

- All filesystem tools are restricted to `workspace_dir`.
- Path traversal is blocked.
- Hidden files and sensitive files are blocked.
- Write tools require dry-run and confirmation.
- Destructive delete tools are intentionally not exposed by default.
- Tool calls are logged to `data/logs/tool_calls.jsonl`.
- Write operations are logged to `data/logs/audit_log.jsonl`.

See `SECURITY.md` before publishing the repository or exposing the API.

## Observability

Logs are JSONL files:

- `data/logs/rag_queries.jsonl`
- `data/logs/tool_calls.jsonl`
- `data/logs/llm_calls.jsonl`
- `data/logs/audit_log.jsonl`
- `data/logs/errors.jsonl`

## LLM / Embedding Extension Points

Implemented clients:

- `MockLLMClient` and `MockEmbeddingClient` for offline demos and tests.
- `OpenAICompatibleLLMClient` for chat completions APIs.
- `OpenAICompatibleEmbeddingClient` for embedding APIs.

Factory functions live in `src/generation/factory.py`. To add Ollama, local SentenceTransformers, or another provider, implement `BaseLLMClient` or `BaseEmbeddingClient`, then register the backend name in the factory. Keep API keys in environment variables or `.env`; `.env` is ignored by Git.

## Tests

```bash
pytest
```

On Windows PowerShell:

```powershell
.\run_tests.ps1
```

## Phase Status

- Phase 1 supported: project structure, config, mock and OpenAI-compatible LLM/embedding, md/txt/html/pdf/docx/pptx loader fallback, chunking, metadata, vector search, ask with citations, Streamlit, CLI, examples, tests.
- Phase 2 supported: BM25, hybrid retrieval, confidence, evidence checker, citation output, `eval-rag`, real `reindex`.
- Phase 3 supported: Tool Registry, tool calling, dry-run, confirmation, audit log, daily/weekly report agent.
- Phase 3.1 supported: LLM-backed JSON tool planner with schema validation, high-risk dry-run enforcement, planner fallback, and agent run logs.
- Phase 4 supported: Reading RAG path import, URL import, metadata extraction, search, reading list export.
- Phase 5 supported: MCP-like tool schemas/client/server and FastAPI health/search/ask/agent.
- Phase 6 supported: JSONL observability, LLM call logs, error-friendly structured results, API backend doctor command.

Current extension boundaries: Chroma/FAISS persistence, advanced cross-encoder reranker, official MCP SDK transport, production authentication, Docker, and richer API route coverage.

## GitHub Release Checklist

- `.env` is ignored; publish `.env.example` only.
- `config.production.yaml` is the API-backed deployment template.
- `PERSONAL_AI_CONFIG=config.production.yaml` can select the production template without overwriting `config.yaml`.
- Review `SECURITY.md` before making the repository public.
- Review `RELEASE_CHECKLIST.md` before tagging or publishing.
- Review `ARCHITECTURE.md` for implementation details and interview explanations.
- Optional: run `pip install -e ".[dev]"` and `personal-ai-workspace --help`.
- Run `python -m compileall src app tests`.
- Run `pytest -q`.
- Run `python -m src.cli doctor-llm` in mock mode.
- Run `python -m src.cli doctor-config`.
- Run `docker compose config` if Docker artifacts are included.
- Run `docker compose -f docker-compose.production.yml config` for the production image.
- If publishing with screenshots or demo data, keep only synthetic examples under `examples/`.
- GitHub Actions CI is available in `.github/workflows/ci.yml`.

## Troubleshooting

- If a command cannot find local files, run it from the project root.
- If a write tool does not execute, check whether `dry_run=false` and `confirm=true` were provided.
- If search returns weak results, ingest the sample documents first.
- If PDF/docx/pptx parsing fails, the loader returns a readable fallback message rather than crashing.

## Roadmap

See `ROADMAP.md`.

## Resume Description

Designed and implemented `personal-ai-workspace`, a local-first Personal AI OS prototype integrating document ingestion, RAG-based QA, agent tool calling, MCP-like tools, evaluation harness, observability, and sandboxed file operations. The system supports BM25/vector/hybrid retrieval, citation grounding, evidence-based refusal, dry-run and human confirmation for write tools, daily/weekly report generation, reading collection management, Streamlit UI, optional FastAPI endpoints, and pytest-based validation.

## Interview Talking Points

- RAG quality is controlled through evidence retrieval, citation grounding, refusal, and evaluation.
- Agent safety is controlled through tool schemas, risk levels, dry-run, confirmation, path guards, and audit logs.
- Agent planning is LLM-backed in production but locally validated before execution.
- MCP makes local tools discoverable and reusable by AI clients.
- Mock LLM/embedding enables offline reproducible demos while preserving extension interfaces.
