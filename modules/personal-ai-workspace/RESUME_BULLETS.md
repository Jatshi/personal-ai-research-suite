# Resume Bullets

## 中文

- 设计并实现 `personal-ai-workspace`，一个本地优先的 Personal AI OS 原型，集成文档知识库、RAG 问答、Agent 工具调用、MCP-like Server、Evaluation Harness、日志可观测性和安全权限控制。
- 实现多格式文档解析与索引流程，支持 Markdown、TXT、HTML、PDF、Word、PPT 等材料导入，基于 BM25、mock 向量检索和 Hybrid Search 提升知识检索质量。
- 构建 Agent Harness，支持工具注册、JSON Schema 风格参数声明、risk_level、dry-run、人类确认、audit log 和 workspace 路径沙箱，降低本地文件操作风险。
- 设计 grounded QA 机制，所有回答必须基于 evidence chunks，并输出 citation、confidence score；证据不足时明确拒答，减少幻觉风险。
- 实现 Reading RAG 与周报 Agent，支持阅读材料导入、主题阅读清单生成、todo/notes 驱动的日报周报生成，并提供 Streamlit UI、CLI、FastAPI 基础接口和 pytest 测试。

## English

- Designed and implemented `personal-ai-workspace`, a local-first Personal AI OS prototype integrating document ingestion, RAG-based QA, agent tool calling, MCP-like tools, evaluation harness, observability, and sandboxed file operations.
- Built a multi-format ingestion and indexing pipeline for Markdown, TXT, HTML, PDF, Word, and PowerPoint documents, combining BM25, mock vector retrieval, and hybrid ranking for local knowledge search.
- Developed an Agent Harness with tool registration, schema-style tool specs, risk levels, dry-run execution, human confirmation, audit logs, and workspace path guards for safer local automation.
- Implemented grounded QA with evidence chunks, citations, confidence scoring, and evidence-based refusal to reduce hallucination risk.
- Added Reading RAG and report agents for article import, topic reading-list generation, todo/notes-driven daily and weekly reports, with Streamlit UI, CLI, optional FastAPI endpoints, and pytest validation.

