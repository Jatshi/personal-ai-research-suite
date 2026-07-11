# Phase 6 完成度验收

本文档将仓库中可由代码和测试证明的实现，与必须依赖外部
OpenAI-compatible 服务的验证明确区分。未实际连接 provider 的能力不会被表述为
已完成真实调用验证。

## 仓库内可证明的范围

| 阶段 | 已交付证据 | 本地验证 |
|---|---|---|
| 6A 高级 RAG | 查询改写、上下文压缩、CRAG、多跳检索及 trace | `test_phase6_rag.py`、`test_api.py` |
| 6B Agent | 原生 tool schema、ReAct、恢复降级、三层记忆 | `test_phase6_agent.py`、`test_llm_tool_planner.py` |
| 6C MCP | FastMCP、官方 Resources/Prompts、legacy 诊断入口 | MCP 模块测试、`doctor-mcp` |
| 6D GraphRAG | SQLite/NetworkX 图索引及可选 LightRAG 适配器 | `test_graphrag.py`、可选生产集成测试 |
| 6E 多 Agent | `AgentRole`、`Task`、`Crew` 与五角色研究工作流 | `test_multi_agent.py` |
| 6F 评估 | 确定性评估、A/B 对比、可选 RAGAS 适配器 | `test_evaluation*.py` |
| 6G 产品 UI | 十个 Next.js 路由、REST/SSE、安全跨模块 bridge、响应式/主题/Toast | `npm run build`、生产模式浏览器 smoke |

## 安全证据

- 文件整理必须先 dry-run，再取得短期审批令牌；执行前会重算计划哈希，并继续使用
  sibling 模块的审计与 rollback。
- 浏览器上传有扩展名、大小和 workspace 限制。
- 设置更新只能修改白名单字段，先预览再明确确认。
- MCP 正式 `serve` 必须使用官方 SDK；旧 stdio 仅通过 `legacy-serve` 提供迁移诊断。

## 复现本地验收

```powershell
cd personal-ai-research-suite
.\scripts\pre_publish_check.ps1
.\scripts\test_all.ps1
```

该套件覆盖 Academic RAG、Personal Agent Workspace、Personal AI Workspace、
Local MCP Toolkit 以及 Next.js 生产构建。

## 外部 Provider Gate

没有凭据时，以下内容不能诚实声明为已完成真实调用验证：

```powershell
cd modules\personal-ai-workspace
$env:OPENAI_API_KEY = "..."
$env:OPENAI_BASE_URL = "https://provider.example/v1"
.\run_production_check.ps1 -CallApi
```

配置真实服务后，还应在保留集上运行 RAGAS，并执行 query rewrite、CRAG、ReAct
原生工具调用与 MCP bridge 的 live smoke。仓库不保存 API key；离线 demo 和回归套件
也不依赖 API key。
