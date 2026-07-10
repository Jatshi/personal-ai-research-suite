# Architecture

`local-mcp-toolkit` exposes local capabilities through the official MCP Python SDK.

## Tool Layers

```text
MCP SDK client (stdio)
        |
        v
ToolRegistry
        |
        +-> RAG tools
        +-> safe filesystem tools
        +-> code intelligence tools
        |
        v
audit logs + security logs
```

## RAG Backends

Two RAG modes are supported:

- `rag.backend: mock`: offline sample KB from `examples/sample_kb`.
- `rag.backend: local_project`: forwards calls to another local RAG project exposing compatible JSON CLI commands.

The `local_project` adapter is how this toolkit connects to `personal-ai-workspace` or `personal-academic-rag-workspace`. If `rag.project_config` is set, it is passed to the target process as `PERSONAL_AI_CONFIG`, so the target RAG project can run with `config.production.yaml` without overwriting its default config.

```text
MCP client -> ask_knowledge_base tool
           -> LocalCliRagAdapter
           -> python -m src.cli ask in target RAG project
           -> structured answer + confidence + citations
```

For write-like RAG management operations, the same adapter preserves dry-run/confirm semantics:

```text
add_document -> dry-run plan by default
add_document + dry_run=false + confirm=true -> target `python -m src.cli ingest`
delete_document + dry_run=false + confirm=true -> target `python -m src.cli delete-doc`
```

## Filesystem Safety

Filesystem tools are guarded by:

- workspace path restriction
- path traversal blocking
- symlink escape blocking
- hidden directory blocking
- sensitive filename blocking
- dry-run and confirmation for writes

## MCP Runtime

`serve` requires the official `mcp.server.fastmcp.FastMCP` runtime. It exposes
tools, document/log resources, and reusable prompts. The old JSON-lines protocol
is retained only behind the explicit `legacy-serve` diagnostic command and is not
a production fallback.

Use:

```bash
python -m src.cli doctor-mcp
```

to inspect the active runtime mode.

## Observability

Tool calls are written to `data/logs/mcp_tool_calls.jsonl`; security events are written to `data/logs/security_audit.jsonl`. Logs are ignored by Git.
