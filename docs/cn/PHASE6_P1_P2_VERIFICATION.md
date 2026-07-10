# Phase 6 P1/P2 验证状态

本文档明确区分已实现并在本地验证的功能，以及需要外部依赖和
OpenAI-compatible 模型服务才能完成的生产验证 gate。

## 已在本地验证

- GraphRAG：SQLite/NetworkX 图索引，以及 `graphrag`、`hybrid+graphrag`
  检索模式。
- 多 Agent Crew：Reader、Method、Experiment、Critic、Writer 五个角色，
  共享 evidence，并支持角色级 LLM 覆盖配置。
- 评估：确定性检索评估与隔离的配置 A/B 对比。
- 产品 API：dashboard 汇总、文档详情、汇总 JSONL 可观测性、公开设置、
  REST/SSE RAG 与 Agent 端点。
- 产品 UI：Next.js 生产构建、浏览器验证过的 SSE RAG 问答及 evidence/trace、
  以及 dry-run 文件整理 bridge。
- 跨模块 bridge：仅接受 `workspace/...` 路径；文件整理调用不会接收
  `--execute` 或 `--yes`；论文检查仅生成报告。

复现本地回归：

```powershell
.\scripts\test_all.ps1
```

## 可选生产验证 Gate

以下功能要求安装 production extra 并配置模型服务凭据：

```powershell
cd modules\personal-ai-workspace
pip install -e ".[production]"
$env:OPENAI_API_KEY = "..."
$env:OPENAI_BASE_URL = "https://provider.example/v1"
```

1. 设置 `graphrag.backend: lightrag`，通过 `POST /graph/build` 构建 collection，
   再通过 `POST /graph/ask` 查询。
2. 在带有效 reference 的保留集上执行
   `python -m src.cli eval-rag --engine ragas --dataset ...`。
3. 使用真实模型服务完成 query rewrite、CRAG、ReAct 工具调用、MCP bridge 与
   浏览器工作台 smoke test。

仓库包含可选集成测试；当 LightRAG/RAGAS 未安装时，测试会显式 skip，
而不是伪造通过结果。

## 已验证的 Production Extra 组合

隔离验证环境已通过 optional integration test，使用的版本为：

- `lightrag-hku 1.5.4`
- `ragas 0.4.3`
- `langchain-openai 1.3.4`
- `langchain-community 0.3.31`

`langchain-community 0.4.x` 与 RAGAS 0.4.3 不兼容，因为它移除了
RAGAS 仍会引用的 VertexAI 导入路径。因此 production extra 固定为
`>=0.3.31,<0.4`。
