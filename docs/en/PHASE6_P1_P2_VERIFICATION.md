# Phase 6 P1/P2 Verification

This document distinguishes implemented, locally verified features from optional
production gates that require external packages and an OpenAI-compatible provider.

## Verified Locally

- GraphRAG: SQLite/NetworkX graph index and `graphrag` / `hybrid+graphrag`
  retrieval modes.
- Multi-agent crew: Reader, Method, Experiment, Critic, and Writer roles with
  shared evidence and role-level LLM overrides.
- Evaluation: deterministic retrieval evaluation and isolated configuration A/B
  comparison.
- Product API: dashboard summary, document detail, merged JSONL observability,
  public settings, REST/SSE RAG and Agent endpoints.
- Product UI: Next.js production build, browser-tested SSE RAG answer with
  evidence/trace, and a dry-run File Organizer bridge.
- Cross-module bridge: only `workspace/...` paths are accepted; organizer calls
  cannot receive `--execute` or `--yes`; thesis calls are report-only and batch
  paper reading exports derived notes without modifying source papers.

Reproduce the local regression:

```powershell
.\scripts\test_all.ps1
```

## Optional Production Gates

The following require the production extras and configured provider credentials:

```powershell
cd modules\personal-ai-workspace
pip install -e ".[production]"
$env:OPENAI_API_KEY = "..."
$env:OPENAI_BASE_URL = "https://provider.example/v1"
```

1. Set `graphrag.backend: lightrag`, build a collection with `POST /graph/build`,
   then query it with `POST /graph/ask`.
2. Run `python -m src.cli eval-rag --engine ragas --dataset ...` against a held-out
   dataset with non-empty references.
3. Run real-provider smoke tests for query rewriting, CRAG, ReAct tool calling,
   MCP bridge calls, and the browser workbench.

The repository includes optional integration tests. They are skipped rather than
falsely passed when LightRAG/RAGAS are not installed.

## Verified Production Extra Set

The isolated verification environment passed the optional integration tests with:

- `lightrag-hku 1.5.4`
- `ragas 0.4.3`
- `langchain-openai 1.3.4`
- `langchain-community 0.3.31`

`langchain-community 0.4.x` is not compatible with RAGAS 0.4.3 because its
VertexAI import path was removed. The production extra therefore pins the
compatible `>=0.3.31,<0.4` range.
