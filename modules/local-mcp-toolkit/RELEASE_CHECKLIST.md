# Release Checklist

Before publishing this repository:

- Confirm `.env` is not committed.
- Keep the fake secret fixtures under `examples/workspace/docs/`; do not replace them with real secrets.
- Run `.\run_tests.ps1` on Windows or `python -m pytest -q` on Linux/macOS.
- Run `python -m src.cli doctor-mcp`.
- Run `python -m src.cli doctor-rag`.
- Run `python -m src.cli doctor-config`.
- Run `python -m src.cli smoke-test`.
- For real RAG mode, set `LOCAL_MCP_CONFIG=config.local_project.example.yaml` or copy that template to `config.yaml`.
- For production bridge mode, set `LOCAL_MCP_CONFIG=config.local_project.production.yaml` and run `.\run_bridge_check.ps1`.
- If the target RAG project is production-configured but CI has no API key, run `.\run_bridge_check.ps1 -AllowMissingSecrets` as a wiring check.
- Verify `local_project` mode can search, ask, dry-run add document, and confirmed delete only when intended.
- Configure LLM/API secrets only in the target RAG project, not in this toolkit.
- Review `SECURITY.md`.
- Verify GitHub Actions CI passes.
