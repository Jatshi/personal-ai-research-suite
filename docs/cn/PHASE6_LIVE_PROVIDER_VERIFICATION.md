# Phase 6 真实 Provider 验证记录

日期：2026-07-12

本记录覆盖已配置 OpenAI-compatible Provider 的真实调用验证。不包含任何凭据、端点密钥或私有源材料。

## 通过的验证

| 范围 | 验证方式 | 结果 |
|---|---|---|
| Provider 客户端 | `run_production_check.ps1 -CallApi` | Chat completion 与 embedding 均成功。 |
| 高级 RAG | 开启 HyDE、CRAG、多跳的 CLI 问答 | 返回有依据的回答和引用；CRAG 为 high；包含两跳检索 trace。 |
| 原生 ReAct | 只读工作区检查 | 使用标准 OpenAI tool-call 历史；完成一次工具观察并正常结束。 |
| 官方 MCP | MCP doctor 与本地 RAG Bridge 检查 | FastMCP 的 tools、resources、prompts 与 RAG Bridge 均成功。 |
| RAGAS | `eval-rag --engine ragas` | 真实评估器与工作区 embedding 适配器均执行完成。 |

## 评估语义

RAGAS 的回答质量指标只使用 `should_answer: true` 且包含非空 `reference` 的样例。拒答样例不进入这些指标，因为 faithfulness 与 context recall 不能衡量拒答质量；拒答由确定性的 refusal accuracy 评估覆盖。非有限的 RAGAS 聚合值会序列化为 JSON `null`，并在 `undefined_metrics` 中明确列出。

## 复现方式

```powershell
cd modules\personal-ai-workspace
.\run_production_check.ps1 -CallApi
$env:PERSONAL_AI_CONFIG = "config.production.yaml"
python -m src.cli eval-rag --engine ragas --dataset examples/sample_eval/phase6_rag_eval.jsonl
```
