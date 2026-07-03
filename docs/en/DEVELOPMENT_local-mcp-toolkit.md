# Development: local-mcp-toolkit

## Architecture

```text
MCP client -> server -> ToolRegistry -> adapters/tools -> local resources
```

## Key Modules

- `src/mcp_servers/`: combined, rag, filesystem, and code servers.
- `src/tools/`: tool definitions and execution logic.
- `src/rag/adapters.py`: mock KB and local RAG project bridge.
- `src/filesystem/`: safe file read/write tools.
- `src/code/`: code repository search, read, and summarization.
- `src/safety/`: path restrictions, sensitive-file checks, audit logs.
- `src/config/`: config loading and path resolution.

## What MCP Solves Here

An LLM should not directly access your filesystem or code repositories. The MCP-style layer provides:

- Tool discovery.
- Parameter schemas.
- Structured results.
- Safety policies.
- Audit logs.
- A protocol boundary between model clients and local capabilities.

## RAG Bridge

`local-mcp-toolkit` supports two RAG backends:

- mock/sample KB for offline demos and tests.
- local_project adapter that calls a local RAG CLI for search, ask, list, add, and delete.

This keeps the MCP layer decoupled from a specific RAG implementation.

## Production Readiness

- `doctor-mcp` checks whether FastMCP is available.
- A minimal JSON-stdio fallback keeps offline tests runnable.
- `doctor-rag` verifies that the RAG backend can search and answer.
- File writes default to dry-run.
- Path and sensitive-file checks run before tool execution.

## Interview Talking Points

- Difference between MCP and a normal HTTP API.
- Why a tool protocol layer needs a safety sandbox.
- How local RAG can be exposed to external model clients.
- Why adapters reduce coupling.
- Why a minimal fallback improves testability.
