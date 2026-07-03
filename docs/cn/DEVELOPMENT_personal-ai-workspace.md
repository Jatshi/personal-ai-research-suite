# 开发文档：personal-ai-workspace

## 架构定位

`personal-ai-workspace` 是集成层，比单独 RAG 或单独 Agent 更接近完整产品：

```text
Document KB + RAG + Agent Harness + FastAPI + Streamlit + MCP-like server + Evaluation + Observability
```

## 核心模块

- `src/indexing/`：文档索引、SQLite/Chroma 后端。
- `src/retrieval/`：BM25、vector、hybrid retrieval。
- `src/generation/`：mock/OpenAI-compatible LLM 与 embedding。
- `src/agents/`：LLM tool planner 和 personal assistant agent。
- `src/tools/`：知识库、todo、报告、写入工具。
- `src/api/`：FastAPI 服务。
- `src/mcp/`：MCP-like JSON stdio server。
- `src/evaluation/`：RAG/Agent eval。
- `src/observability/`：RAG、tool、audit、LLM、error 日志。

## 生产化设计

- `config.production.yaml` 切换真实 LLM/embedding/Chroma/API auth。
- `.env.example` 只放模板，不提交真实 key。
- `doctor-config` 检查生产配置、目录、依赖、安全开关。
- `doctor-llm --call-api` 检查真实 provider。
- FastAPI 使用 token 保护。
- 删除文档默认 dry-run，必须 `--confirm`。
- Agent 高风险工具默认 dry-run。

## Agent Harness

Agent Harness 的流程：

1. 接收目标。
2. LLM planner 生成 JSON tool plan。
3. 校验 tool 是否存在、参数是否合法。
4. 高风险工具强制 dry-run。
5. 执行工具。
6. 记录 trace、日志、最终报告。

## 观测与评估

生产 AI 系统不能只看“能回答”。该项目记录：

- RAG query log。
- tool call log。
- audit log。
- LLM call log。
- error log。

评估覆盖：

- 检索命中。
- 引用存在。
- 拒答准确性。
- Agent 工具选择。

## 面试可讲点

- 为什么把 RAG、Agent、API、观测放在同一个 workspace。
- 为什么需要 API auth。
- 为什么真实 LLM planner 需要 JSON 计划校验。
- 为什么删除/写入必须 dry-run。
- 如何通过 eval 证明 RAG 不是“看起来能用”。
