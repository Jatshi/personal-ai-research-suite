# Architecture

`personal-ai-workspace` is organized around one shared registry and a small set of replaceable backends.

## Runtime Flow

```text
documents / notes / reading items
        |
        v
loaders -> chunker -> SQLite metadata/chunk store
        |              |
        |              +-> BM25 keyword retrieval
        v
embedding client -> SQLite vector backend or Chroma vector backend
        |
        v
hybrid retriever -> evidence checker -> LLM answer generator -> citations
```

## Phase 6 Retrieval Controls

`AdvancedRetriever` wraps the hybrid retriever without replacing it. Configuration
can enable query rewriting (HyDE or decomposition), token/extractive context
compression, CRAG routing, and bounded multi-hop retrieval. Every request returns
a retrieval trace. Low CRAG confidence always follows the grounded refusal path.

## LLM And Embedding Backends

The project uses factory functions in `src/generation/factory.py`.

- `MockLLMClient` and `MockEmbeddingClient` keep tests and offline demos deterministic.
- `OpenAICompatibleLLMClient` and `OpenAICompatibleEmbeddingClient` work with OpenAI and compatible providers.
- API keys are read from environment variables defined in config, never hard-coded.

## Vector Store Backends

SQLite always stores document metadata and chunks. Vector retrieval is configurable:

- `vector_store.backend: sqlite`: lightweight local default.
- `vector_store.backend: chroma`: persistent production semantic retrieval.

Changing embedding models or vector-store backend requires reindexing.

## Agent Execution

The agent does not execute arbitrary model text. It follows this pipeline:

```text
user goal
  -> LLM tool planner returns JSON
  -> local validator filters unknown tools
  -> high-risk tools are forced to dry-run
  -> ToolRegistry executes approved calls
  -> final report is generated from tool outputs
```

This keeps LLM planning flexible while preserving deterministic local safety controls.

`ReActAgent` is an optional execution mode. It uses native OpenAI-compatible tool
calls, feeds each observation back to the model, detects repeated actions, records
recovery/fallback decisions, and cannot bypass `ToolRegistry` approval checks.

## Memory

Session messages provide short-term context; the ReAct state is work memory; and
an opt-in SQLite `memories` table stores filtered long-term preferences and durable
task conclusions. Potential secrets and sensitive path material are rejected before
durable storage.

## API And UI

- CLI, FastAPI, Streamlit, and MCP-like stdio all call the same tool/retrieval layers.
- FastAPI request bodies are Pydantic-validated.
- API token protection can be enabled with `server.api_auth_enabled: true`.

## Observability

JSONL logs are written under `data/logs/`:

- RAG queries
- tool calls
- LLM calls
- agent runs
- audit/error events

These logs are intentionally local and ignored by Git.
