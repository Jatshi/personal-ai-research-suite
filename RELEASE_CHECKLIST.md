# Release Checklist

Before publishing `personal-ai-research-suite` to GitHub:

## Repository Hygiene

- Run `.\scripts\sync_projects.ps1` to refresh module copies.
- Run `.\scripts\pre_publish_check.ps1`.
- Confirm no `.env`, raw private data, runtime `data/`, cache, SQLite database, vector index, or `__pycache__` files are included.
- Confirm `.env.example` contains templates only.

## Tests

- Run `.\scripts\test_all.ps1`.
- Expected current baseline:
  - `personal-academic-rag-workspace`: 15 tests.
  - `personal-agent-workspace`: 18 tests.
  - `personal-ai-workspace`: 40 tests.
  - `local-mcp-toolkit`: 21 tests.

## Production LLM Readiness

- In `modules/personal-ai-workspace`, run:

```powershell
$env:PERSONAL_AI_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
$env:PERSONAL_AI_API_TOKEN="replace-with-strong-token"
.\run_production_check.ps1 -CallApi
```

- In `modules/local-mcp-toolkit`, run:

```powershell
$env:LOCAL_MCP_CONFIG="config.local_project.production.yaml"
.\run_bridge_check.ps1
```

If no real API key is available in CI, run the non-paid wiring checks:

```powershell
.\modules\personal-ai-workspace\run_production_check.ps1 -AllowMissingSecrets
.\modules\local-mcp-toolkit\run_bridge_check.ps1 -AllowMissingSecrets
```

## Documentation

- Confirm root `README.md` explains the four-module relationship.
- Confirm `docs/cn/` and `docs/en/` both include system overview, usage docs, and development docs.
- Confirm each module README remains runnable from its module directory.

## Security

- Do not upload real doctoral/private materials.
- Do not upload API keys.
- Keep write/delete operations dry-run by default.
- Review each module `SECURITY.md` when present.
