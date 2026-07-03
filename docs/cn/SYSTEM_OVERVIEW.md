# 系统总览

## 四个项目是否有关联

有关联，但不是互相强耦合。它们采用“独立项目 + 可组合系统”的关系：

- `personal-academic-rag-workspace`：专注个人/学术知识库 RAG。负责导入论文、博士材料、会议记录、简历、项目材料，完成解析、切块、索引、混合检索、重排、引用问答和 Academic RAG。
- `personal-agent-workspace`：专注本地 Agent 工作流。负责文件整理、博士论文收尾检查、多 Agent 论文阅读、日报/周报和任务规划，强调 Tool Calling、安全审批、dry-run、审计日志。
- `personal-ai-workspace`：综合型 Personal AI OS。把 RAG、Agent Harness、FastAPI、Streamlit、MCP-like server、评估、日志观测、阅读管理集成在一个更完整的应用里。
- `local-mcp-toolkit`：工具协议层。把本地 RAG、文件系统、代码仓库能力暴露成 MCP 风格工具，便于 Claude Desktop、IDE Agent 或其他模型客户端调用。

## 联合使用方式

推荐关系：

1. 用 `personal-academic-rag-workspace` 建立最专业的学术知识库。
2. 用 `personal-agent-workspace` 完成本地文件整理、论文检查和个人工作流。
3. 用 `personal-ai-workspace` 作为统一的 Web/API 工作台。
4. 用 `local-mcp-toolkit` 把前面系统能力暴露给外部 AI 客户端。

## 总体数据流

```text
本地材料
  -> 文档解析
  -> chunking
  -> embedding / BM25 index
  -> hybrid retrieval
  -> reranker
  -> evidence checker
  -> LLM answer with citations
  -> Agent tool calls / MCP tools / UI/API
```

## 为什么不是一个巨大单体

面试时可以这样解释：

- RAG、Agent、MCP 是三个不同职责边界。
- 如果写成一个单体，工具调用、安全策略、检索评估、API 服务会互相污染。
- 现在采用 monorepo 包装，每个子系统保持独立部署和测试，同时通过 CLI/API/MCP 组合。
- 这体现的是工程上的 bounded context 和 integration layer 思维。

## 面试重点

- RAG 不等于训练模型，核心是高质量检索、重排、证据构造和引用校验。
- Agent 不等于 chatbot，关键是工具注册、状态管理、审批、安全执行和审计。
- MCP 是工具协议层，解决“模型如何发现并调用本地能力”的问题。
- 生产化不是只接 LLM API，还包括配置、诊断、测试、日志、回滚、文档、CI、Docker 或发布流程。
