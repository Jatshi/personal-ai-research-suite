# 使用文档：local-mcp-toolkit

## 定位

这是 MCP 风格的本地工具网关。它把 RAG、文件系统、代码仓库能力封装成结构化工具，供 MCP-compatible 客户端或本地 Agent 调用。

## 安装

```powershell
cd modules\local-mcp-toolkit
pip install -r requirements.txt
pip install -e ".[dev]"
```

## 快速检查

```powershell
python -m src.cli inspect-tools
python -m src.cli doctor-config
python -m src.cli doctor-mcp
python -m src.cli doctor-rag
python -m src.cli smoke-test
```

## 启动 MCP Server

```powershell
python -m src.cli serve --server combined
```

也可以单独启动：

```powershell
python -m src.cli serve --server rag
python -m src.cli serve --server filesystem
python -m src.cli serve --server code
```

## 调用工具

```powershell
python -m src.cli test-client --tool list_files
python -m src.cli test-client --tool search_documents --query "RAG 是什么？"
python -m src.cli test-client --tool ask_knowledge_base --query "请总结知识库内容"
python -m src.cli test-client --tool list_repo_tree --repo-path ./examples/workspace/sample_repo
```

## 连接真实 RAG 项目

使用 `config.local_project.example.yaml`，它会把 RAG 调用转发到 `personal-ai-workspace` 或其他本地 RAG CLI。

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.example.yaml"
python -m src.cli doctor-rag
```

如果下游 RAG 使用真实 LLM API，需要在下游项目设置对应 config 和 API key。

生产桥接模板会把请求转发到 `personal-ai-workspace/config.production.yaml`：

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.production.yaml"
python -m src.cli doctor-rag
.\run_bridge_check.ps1
```

如果当前机器没有真实 API key，可以运行：

```powershell
.\run_bridge_check.ps1 -AllowMissingSecrets
```

## 安全机制

- 文件工具限制在 workspace 内。
- 默认阻止路径穿越。
- 默认阻止敏感文件。
- 写操作需要 dry-run 和确认。
- 工具调用写入 JSONL 日志。

## 适合场景

- 给 Claude Desktop 或 IDE Agent 暴露本地工具。
- 统一管理本地 RAG、文件、代码仓库工具。
- 测试 MCP tool schema 和 tool calling 安全策略。
