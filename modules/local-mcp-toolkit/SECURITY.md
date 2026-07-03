# Security Policy

## Secrets

Do not commit real `.env`, API keys, personal documents, or private repositories. The fake files in `examples/workspace/docs/` are test fixtures used to verify sensitive-file blocking.

## Filesystem Tools

Filesystem tools are restricted to `app.workspace_dir`, block hidden/sensitive files by default, and require dry-run plus confirmation for writes. Keep these protections enabled for shared environments.

## RAG Bridge

`rag.backend=local_project` forwards queries to another local RAG project. Configure secrets in the target project, not in this toolkit. Do not expose the MCP server to untrusted clients without an external access-control layer.

## Reporting Issues

If you discover a vulnerability, open a private security advisory or contact the repository owner. Do not publish exploit details before a fix is available.
