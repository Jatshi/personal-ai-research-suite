# local-mcp-toolkit

`local-mcp-toolkit` is a local MCP-style toolkit that exposes a safe filesystem, a local knowledge base, and local code repository intelligence as structured tools. It is designed for MCP-compatible clients, local agent experiments, and security-focused tool-calling systems. It can run against the built-in offline sample KB or forward RAG calls to a real local RAG project that uses LLM and embedding APIs.

## What MCP Means Here

MCP (Model Context Protocol) standardizes how model clients call tools. This project uses the official Python `mcp` SDK when it is installed (`mcp.server.fastmcp.FastMCP`). For offline development environments where the SDK has not yet been installed, the same CLI falls back to a minimal JSON-stdio demo server so tests and examples remain runnable.

## Features

- RAG Knowledge Base tools: search, ask with citations, list collections/documents, summaries, add/delete document with dry-run and confirm.
- Safe Filesystem tools: list, read, search, write with workspace sandbox, sensitive-file blocking, dry-run, confirm, audit logs.
- Local Code Repository tools: tree, search, read code, summarize modules, find TODO/FIXME/HACK/NOTE, repo summary, issue and PR draft generation.
- Unified `ToolSpec` and `ToolRegistry`.
- JSONL audit logs.
- Prompt injection risk detection.
- Minimal client for testing tool calls.
- Example workspace, mock KB, and sample repository.
- Pytest security and tool tests.

## Tech Stack

- Python
- YAML config via `config.yaml`
- JSON/JSONL local data and logs
- pytest
- Official Python MCP SDK via FastMCP, with a minimal JSON-stdio fallback

## Install

```bash
cd D:\博士毕业论文\local-mcp-toolkit
pip install -r requirements.txt
```

Editable install with console script:

```bash
pip install -e ".[dev]"
local-mcp-toolkit --help
```

This repository is packaged as a source application. The console script is intended for editable/source checkouts and loads `src/cli.py` from the repository root to avoid top-level `src` package collisions with other local projects.

## Quick Start

```bash
python -m src.cli inspect-tools
python -m src.cli doctor-mcp
python -m src.cli doctor-rag
python -m src.cli test-client --tool list_files
python -m src.cli test-client --tool search_documents --query "RAG 是什么？"
python -m src.cli test-client --tool list_repo_tree --repo-path ./examples/workspace/sample_repo
pytest
```

## Start MCP Server

```bash
python -m src.cli serve --server combined
python -m src.cli serve --server rag
python -m src.cli serve --server filesystem
python -m src.cli serve --server code
```

On Windows PowerShell:

```powershell
.\run_mcp.ps1
```

The stdio server accepts newline-delimited JSON:

```json
{"method":"tools/list"}
{"method":"tools/call","tool":"list_files","arguments":{"path":".","recursive":true}}
```

After `pip install -r requirements.txt`, `serve` uses FastMCP. Without the optional SDK installed, it prints `mode=minimal-json-stdio` and accepts the JSON lines above for local smoke tests.

Check the MCP runtime mode:

```bash
python -m src.cli doctor-mcp
```

This reports whether the official `mcp.server.fastmcp.FastMCP` transport is installed, the active fallback mode, and the exposed tool list.

Validate the whole config before starting services:

```bash
python -m src.cli doctor-config
```

## Minimal Client

```bash
python src/clients/minimal_mcp_client.py --list-tools
python src/clients/minimal_mcp_client.py --tool list_files --args "{\"path\":\".\",\"recursive\":true}"
python src/clients/minimal_mcp_client.py --tool read_file --args "{\"path\":\"../secret.txt\"}"
```

## RAG Backend Doctor

Check whether the configured RAG backend is reachable:

```bash
python -m src.cli doctor-rag
```

For the offline sample backend this searches `examples/sample_kb`. For `rag.backend=local_project`, it verifies that the target project can answer the compatible `search` CLI command.
It also performs a lightweight `ask_knowledge_base` call so the answer/confidence path is checked, not only retrieval.

## Servers

For a deeper system overview, see `ARCHITECTURE.md`.

### Local Knowledge Base MCP Server

Uses `examples/sample_kb/*.json` as the offline sample RAG backend. It returns structured search results, citations, confidence scores, and evidence sufficiency. For real LLM-backed answers, set `rag.backend=local_project` and point `rag.project_path` to a local RAG project such as `personal-ai-workspace` or `personal-academic-rag-workspace`.

### Safe Filesystem MCP Server

All paths are restricted to `app.workspace_dir`. Reads are text-only. Writes require `dry_run=false` and `confirm=true`, do not overwrite existing files unless `overwrite=true`, and write audit/rollback information.

### Local Git/Code Repository MCP Server

Reads only repositories under workspace. It skips `.git`, `node_modules`, virtualenvs, caches, and hidden directories. It extracts functions/classes/imports with rule-based code intelligence.

## Tool Schema

Each tool declares:

```python
ToolSpec(
    name="...",
    description="...",
    input_schema={...},
    output_schema=None,
    risk_level="low|medium|high",
    requires_confirmation=True|False,
    category="rag|filesystem|code",
)
```

Every call returns structured JSON with either `success=true` and `data`, or `success=false` and `error`.

## Security

- Workspace restriction blocks `../`, absolute paths outside workspace, parent/system directory access, and symlink escape.
- Sensitive file guard blocks `.env`, `*.key`, `*.pem`, `*.crt`, `*.p12`, `id_rsa`, `id_ed25519`, `credentials.json`, `secrets.*`, `*.secret`, `*.token`.
- Hidden paths are blocked by default.
- Writes are dry-run by default and require `confirm=true`.
- Existing files are not overwritten unless `overwrite=true`.
- Tool calls log to `data/logs/mcp_tool_calls.jsonl`.
- Security events log to `data/logs/security_audit.jsonl`.
- Prompt injection guard warns or blocks basic patterns such as “ignore previous instructions”, secret exfiltration requests, workspace escape requests, and mass delete/overwrite instructions.

The files `examples/workspace/docs/fake.env` and `fake_key.pem` contain fake test data only and exist to prove sensitive-file blocking.

See `SECURITY.md` before publishing the repository or exposing the toolkit to untrusted clients.

## Connect Existing RAG

Use `rag.backend=local_project` for a CLI-compatible local RAG project, or implement a new adapter in `src/rag/adapters.py` for direct database access. Keep the public methods compatible with `MockKnowledgeBase`.

### Use A Real Local RAG Project

`local-mcp-toolkit` can expose another local RAG project as MCP tools. The target project must support JSON CLI commands similar to:

```bash
python -m src.cli search --query "..." --mode hybrid --top-k 5
python -m src.cli ask --query "..." --top-k 5
python -m src.cli list-docs
python -m src.cli show-doc --doc-id <doc_id>
```

For example, after configuring `personal-ai-workspace` with real OpenAI-compatible LLM and embedding APIs, edit `config.yaml`:

```yaml
rag:
  backend: local_project
  project_path: ../personal-ai-workspace
  project_config: config.yaml
```

Then start the MCP server:

```bash
python -m src.cli serve --server rag
```

Calls to `search_documents` and `ask_knowledge_base` will be forwarded to that project. If the target RAG project uses a real LLM API, the MCP tool result will also use the real LLM answer, citations, confidence, and evidence returned by the target project.

You can also start from the provided template:

```bash
copy config.local_project.example.yaml config.yaml
```

Or keep the default sample config untouched and select the real RAG bridge config per process:

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.example.yaml"
python -m src.cli doctor-rag
python -m src.cli serve --server rag
```

Set `rag.project_config: config.production.yaml` when you want the target `personal-ai-workspace` process to use its production LLM/Chroma config.

For a ready production bridge template, use:

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.production.yaml"
python -m src.cli doctor-rag
```

Or run the bridge check script:

```powershell
.\run_bridge_check.ps1
```

If the target `personal-ai-workspace` production config is missing API secrets, use:

```powershell
.\run_bridge_check.ps1 -AllowMissingSecrets
```

## MCP Client Configuration

For a client that supports command-based stdio servers, point it to:

```bash
python -m src.cli serve --server combined
```

Use the project directory as the working directory so `config.yaml` resolves correctly.

Production `serve` requires the official `mcp` Python SDK. `legacy-serve` exists
only for migration diagnostics and must not be used in client configuration.

Example client configuration:

```json
{
  "mcpServers": {
    "scholarmind": {
      "command": "python",
      "args": ["-m", "src.cli", "serve", "--server", "combined"],
      "cwd": "/absolute/path/to/personal-ai-research-suite/modules/local-mcp-toolkit"
    }
  }
}
```

The server exposes `scholarmind://collections`, document and recent-log resources,
plus `grounded_rag_answer`, `research_summary`, and `safe_file_organization` prompts.

## Docker

```bash
docker compose build
docker compose run --rm mcp python -m src.cli smoke-test
docker compose run --rm mcp python -m src.cli doctor-rag
```

The default container command starts the combined MCP stdio server:

```bash
docker compose run --rm mcp
```

For real LLM-backed RAG, configure the target RAG project's `.env` and `config.yaml`, then set this project's `rag.backend=local_project` and `rag.project_path` to the mounted target path.

## Tests

```bash
pytest
```

On Windows PowerShell:

```powershell
.\run_tests.ps1
```

## Phase Status

- Phase 1 supported: project structure, config, registry, path guard, sensitive guard, audit log, list/read/search/write file, minimal client, README, tests.
- Phase 2 supported: mock KB, search/ask/list/add/delete document tools and tests.
- Phase 3 supported: repo tree, code search/read, module summary, TODO finder, repo summary, issue/PR draft tools and tests.
- Phase 4 supported: prompt injection guard, security docs, expanded tests, client examples, resume description.

Not yet supported: full official MCP SDK transport negotiation, production authentication, binary file parsing, semantic embeddings, live git metadata.

## GitHub Release Checklist

- Keep sample secrets fake; `examples/workspace/docs/fake.env` and `fake_key.pem` are test fixtures only.
- `config.local_project.example.yaml` is the template for connecting a real RAG project.
- `LOCAL_MCP_CONFIG=config.local_project.example.yaml` can select the real RAG bridge template without overwriting `config.yaml`.
- Review `SECURITY.md` before making the repository public.
- Review `RELEASE_CHECKLIST.md` before tagging or publishing.
- Review `ARCHITECTURE.md` for implementation details and interview explanations.
- Optional: run `pip install -e ".[dev]"` and `local-mcp-toolkit --help`.
- Run `python -m compileall src tests`.
- Run `pytest -q`.
- Run `python -m src.cli doctor-mcp`.
- Run `python -m src.cli doctor-config`.
- Run `python -m src.cli smoke-test`.
- Run `python -m src.cli doctor-rag`.
- Run `docker compose config` if Docker artifacts are included.
- If connecting to a real RAG project, document that project's `.env` and `config.yaml` setup instead of storing keys here.
- GitHub Actions CI is available in `.github/workflows/ci.yml`.

## Roadmap

- Add official Python MCP SDK server wrappers.
- Add adapter to `personal-academic-rag-workspace`.
- Add SQLite-backed KB state.
- Add richer AST/codegraph support.
- Add signed audit logs and policy profiles.

## Resume Description

Designed and implemented `local-mcp-toolkit`, a local MCP Server toolkit for exposing personal knowledge bases, safe filesystem access, and local code repositories to MCP-compatible AI clients. The project wraps RAG search and grounded QA as standard MCP-style tools, adds secure filesystem and repository tools for structured file access, code search, module summaries, TODO discovery, and PR/Issue draft generation, and enforces safety through workspace sandboxing, path traversal protection, sensitive-file blocking, dry-run/confirm write operations, prompt-injection checks, and JSONL audit logs.
