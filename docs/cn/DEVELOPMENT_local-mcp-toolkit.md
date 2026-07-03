# 开发文档：local-mcp-toolkit

## 核心架构

```text
MCP client -> server -> ToolRegistry -> adapters/tools -> local resources
```

## 关键模块

- `src/mcp_servers/`：combined、rag、filesystem、code server。
- `src/tools/`：工具定义和执行逻辑。
- `src/rag/adapters.py`：mock KB 与本地 RAG 项目桥接。
- `src/filesystem/`：安全文件读写。
- `src/code/`：代码仓库搜索、读取、摘要。
- `src/safety/`：路径限制、敏感文件检测、审计日志。
- `src/config/`：配置加载和路径解析。

## MCP 在这里解决什么

LLM 不能直接安全地访问你的文件系统或代码仓库。MCP 风格工具层提供：

- 工具发现。
- 参数 schema。
- 统一返回结构。
- 安全策略。
- 审计日志。
- 客户端与本地能力的协议边界。

## RAG Bridge

`local-mcp-toolkit` 可以有两种 RAG 后端：

- mock/sample KB：离线演示和测试。
- local_project：调用本地 RAG 项目 CLI，把 search/ask/list/add/delete 转发出去。

这使 MCP 层不绑定某个具体 RAG 实现。

## 生产化关键点

- `doctor-mcp` 检查 FastMCP 是否可用。
- FastMCP 不可用时使用 minimal JSON-stdio fallback。
- `doctor-rag` 检查 RAG 后端是否可搜索、可问答。
- 文件写操作默认 dry-run。
- 路径和敏感文件检查在工具执行前完成。

## 面试可讲点

- MCP 与普通 HTTP API 的区别。
- 为什么工具协议层需要安全沙箱。
- 如何把本地 RAG 暴露给外部模型客户端。
- 为什么 adapter 设计能降低耦合。
- 为什么需要 minimal fallback 保证离线测试。
