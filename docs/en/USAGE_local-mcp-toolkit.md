# Usage: local-mcp-toolkit

## Purpose

This module is an MCP-style local tool gateway. It exposes RAG, filesystem, and code-repository capabilities as structured tools for MCP-compatible clients or local Agents.

## Install

```powershell
cd modules\local-mcp-toolkit
pip install -r requirements.txt
pip install -e ".[dev]"
```

## Quick Checks

```powershell
python -m src.cli inspect-tools
python -m src.cli doctor-config
python -m src.cli doctor-mcp
python -m src.cli doctor-rag
python -m src.cli smoke-test
```

## Start MCP Server

```powershell
python -m src.cli serve --server combined
```

Or start individual tool groups:

```powershell
python -m src.cli serve --server rag
python -m src.cli serve --server filesystem
python -m src.cli serve --server code
```

## Call Tools

```powershell
python -m src.cli test-client --tool list_files
python -m src.cli test-client --tool search_documents --query "What is RAG?"
python -m src.cli test-client --tool ask_knowledge_base --query "Summarize the knowledge base."
python -m src.cli test-client --tool list_repo_tree --repo-path ./examples/workspace/sample_repo
```

## Connect A Real RAG Project

Use `config.local_project.example.yaml` to forward RAG calls to `personal-ai-workspace` or another local RAG CLI.

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.example.yaml"
python -m src.cli doctor-rag
```

If the downstream RAG project uses a real LLM API, configure its production config and API key separately.

The production bridge template forwards requests to `personal-ai-workspace/config.production.yaml`:

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.production.yaml"
python -m src.cli doctor-rag
.\run_bridge_check.ps1
```

If the current machine has no real API key, run:

```powershell
.\run_bridge_check.ps1 -AllowMissingSecrets
```

## Safety

- Filesystem tools are restricted to the configured workspace.
- Path traversal is blocked.
- Sensitive files are blocked by default.
- Write operations require dry-run and confirmation.
- Tool calls are written to JSONL logs.

## Use Cases

- Expose local tools to Claude Desktop or IDE Agents.
- Centralize local RAG, filesystem, and code tools.
- Test MCP tool schemas and safe tool-calling policies.
