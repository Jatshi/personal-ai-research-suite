# Phase 6 Completion Audit

This audit separates repository-proven implementation from external-provider
verification. It is intentionally evidence-based: a feature is not called
provider-verified unless a configured OpenAI-compatible endpoint was contacted.

## Repository-Proven Scope

| Phase | Delivered evidence | Local verification |
|---|---|---|
| 6A Advanced RAG | `src/retrieval/{query_rewriter,context_compressor,adaptive_router,multi_hop_retriever}.py`; request-scoped FastAPI controls and retrieval traces | `tests/test_phase6_rag.py`, `tests/test_api.py` |
| 6B Agent | native tool schemas, `ReActAgent`, repair/fallback traces, `MemoryStore` | `tests/test_phase6_agent.py`, `tests/test_llm_tool_planner.py` |
| 6C MCP | FastMCP server, official resources/prompts, legacy diagnostic command only | `modules/local-mcp-toolkit/tests`, `doctor-mcp` |
| 6D GraphRAG | SQLite/NetworkX GraphRAG plus optional LightRAG adapter | `tests/test_graphrag.py`, optional production-integration tests |
| 6E Multi-agent | `AgentRole`, `Task`, `Crew`, and the five-role research workflow | `tests/test_multi_agent.py` |
| 6F Evaluation | deterministic evaluation, A/B comparison, optional RAGAS adapter | `tests/test_evaluation*.py` |
| 6G Product UI | ten Next.js routes, REST/SSE workbench, safe sibling bridges, responsive/theme/toast behavior | `npm run build`; browser smoke in production mode |

## Safety Evidence

- File organizer execution requires a dry-run plan, a short-lived approval token,
  plan-hash revalidation, and the sibling module's audit/rollback mechanism.
- Browser uploads are extension and size limited; all indexing stays in the local
  workspace data directory.
- Settings writes use an allowlist, preview, and explicit confirmation.
- MCP production `serve` requires the official SDK; the old stdio runner is only
  available as `legacy-serve`.

## Reproduce The Local Gate

```powershell
cd personal-ai-research-suite
.\scripts\pre_publish_check.ps1
.\scripts\test_all.ps1
```

The current local suite covers Academic RAG, Personal Agent Workspace, Personal
AI Workspace, Local MCP Toolkit, and the Next.js production build.

## External Provider Gate

The following is deliberately not claimed as locally complete without credentials:

```powershell
cd modules\personal-ai-workspace
$env:OPENAI_API_KEY = "..."
$env:OPENAI_BASE_URL = "https://provider.example/v1"
.\run_production_check.ps1 -CallApi
```

With a real provider, also run a held-out RAGAS dataset and the live smoke cases
for query rewriting, CRAG, ReAct native tool calling, and the MCP bridge. No API
key is stored in this repository or required for the offline demo and regression
suite.
