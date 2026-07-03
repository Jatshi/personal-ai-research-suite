# Development: personal-ai-workspace

## Architecture Role

`personal-ai-workspace` is the integration layer:

```text
Document KB + RAG + Agent Harness + FastAPI + Streamlit + MCP-like server + Evaluation + Observability
```

## Key Modules

- `src/indexing/`: document indexing and SQLite/Chroma backends.
- `src/retrieval/`: BM25, vector, and hybrid retrieval.
- `src/generation/`: mock and OpenAI-compatible LLM/embedding clients.
- `src/agents/`: LLM tool planner and personal assistant agent.
- `src/tools/`: KB, todo, report, and write tools.
- `src/api/`: FastAPI service.
- `src/mcp/`: MCP-like JSON stdio server.
- `src/evaluation/`: RAG and Agent evaluation.
- `src/observability/`: RAG, tool, audit, LLM, and error logs.

## Production Design

- `config.production.yaml` enables real LLM, real embeddings, Chroma, and API auth.
- `.env.example` provides templates only.
- `doctor-config` checks config, directories, dependencies, and safety flags.
- `doctor-llm --call-api` verifies the real provider.
- FastAPI endpoints are protected by token auth.
- Document deletion is dry-run by default and requires `--confirm`.
- High-risk Agent tools default to dry-run.

## Agent Harness

Flow:

1. Receive a user goal.
2. LLM planner generates a JSON tool plan.
3. Validate tool names and parameters.
4. Force dry-run for high-risk tools.
5. Execute tools.
6. Record trace, logs, and final report.

## Observability And Evaluation

The system records:

- RAG query logs.
- Tool call logs.
- Audit logs.
- LLM call logs.
- Error logs.

Evaluation covers:

- Retrieval hit rate.
- Citation presence.
- Refusal accuracy.
- Agent tool selection.

## Interview Talking Points

- Why RAG, Agent, API, and observability are integrated.
- Why API auth matters even for local tools.
- Why LLM-generated tool plans need validation.
- Why write/delete operations require dry-run.
- How evaluation prevents “it looks useful” from being the only quality signal.
