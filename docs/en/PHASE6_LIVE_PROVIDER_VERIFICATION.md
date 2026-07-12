# Phase 6 Live Provider Verification

Date: 2026-07-12

This record covers real calls to the locally configured OpenAI-compatible
provider. It contains no credentials, endpoint secrets, or private source data.

## Passed Checks

| Area | Verification | Result |
|---|---|---|
| Provider clients | `run_production_check.ps1 -CallApi` | Chat completion and embeddings succeeded. |
| Advanced RAG | CLI question with HyDE, CRAG, and multi-hop enabled | Grounded answer, citations, high CRAG route, and two-hop retrieval trace. |
| Native ReAct | Read-only workspace inspection | Standard OpenAI tool-call history, one tool observation, normal completion. |
| Official MCP | MCP doctor and local RAG bridge check | FastMCP tools, resources, prompts, and RAG bridge succeeded. |
| RAGAS | `eval-rag --engine ragas` | Real evaluator and workspace embedding adapter completed. |

## Evaluation Semantics

RAGAS answer-quality metrics run only on samples with `should_answer: true` and
a non-empty `reference`. Refusal cases are excluded because faithfulness and
context recall are not refusal-quality metrics; they are covered by the
deterministic refusal-accuracy evaluation. Non-finite RAGAS aggregates are
serialized as JSON `null` and identified in `undefined_metrics`.

## Reproduce

```powershell
cd modules\personal-ai-workspace
.\run_production_check.ps1 -CallApi
$env:PERSONAL_AI_CONFIG = "config.production.yaml"
python -m src.cli eval-rag --engine ragas --dataset examples/sample_eval/phase6_rag_eval.jsonl
```
