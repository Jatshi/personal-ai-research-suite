# System Overview

## Are The Four Projects Related?

Yes. They are related but not tightly coupled. The design is “independent projects + composable system”:

- `personal-academic-rag-workspace`: academic and personal RAG knowledge base. It handles ingestion, parsing, chunking, indexing, hybrid retrieval, reranking, grounded QA, and academic paper analysis.
- `personal-agent-workspace`: local Agent workflow system. It handles file organization, thesis finishing checks, multi-agent paper reading, daily/weekly reports, task planning, tool calling, dry-run safety, approval, and audit logs.
- `personal-ai-workspace`: integrated Personal AI OS. It combines RAG, Agent Harness, FastAPI, Streamlit, MCP-like tools, evaluation, observability, and reading workflows.
- `local-mcp-toolkit`: protocol and tool bridge. It exposes local RAG, filesystem, and code-repository tools to MCP-style clients.

## Recommended Combined Workflow

1. Use `personal-academic-rag-workspace` as the specialized academic knowledge base.
2. Use `personal-agent-workspace` for local file organization, thesis checks, and personal workflows.
3. Use `personal-ai-workspace` as the integrated Web/API workbench.
4. Use `local-mcp-toolkit` to expose capabilities to external model clients.

## High-Level Data Flow

```text
local materials
  -> document parsing
  -> chunking
  -> embedding / BM25 indexing
  -> hybrid retrieval
  -> reranking
  -> evidence checking
  -> LLM answer with citations
  -> Agent tool calls / MCP tools / UI/API
```

## Why Not One Huge Monolith?

A strong interview answer:

- RAG, Agent workflows, and MCP tooling have different responsibility boundaries.
- A monolith would mix retrieval, tool safety, evaluation, and API concerns.
- This suite uses a monorepo wrapper while each module remains independently runnable and testable.
- This demonstrates bounded contexts, integration layers, and production-oriented AI system design.

## Interview Talking Points

- RAG does not normally require training. The core work is retrieval quality, reranking, evidence construction, citation grounding, and evaluation.
- An Agent is not just a chatbot. It needs tool schemas, state, safety policies, dry-run execution, approval, and audit logs.
- MCP is a protocol layer that lets model clients discover and call local tools.
- Production readiness means more than adding an LLM API: configuration, diagnostics, tests, logs, rollback, docs, CI, and deployment matter.
