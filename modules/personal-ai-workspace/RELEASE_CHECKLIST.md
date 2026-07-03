# Release Checklist

Before publishing this repository:

- Confirm `.env` is not committed.
- Keep only synthetic data under `examples/`.
- Run `.\run_tests.ps1` on Windows or `python -m pytest -q` on Linux/macOS.
- Run `python -m src.cli doctor-llm`.
- Run `python -m src.cli doctor-config`.
- Verify FastAPI endpoints: `/health`, `/llm/doctor`, `/kb/docs`, `/rag/search`, `/rag/ask`.
- Verify destructive document deletion stays dry-run unless `confirm=true` / `--confirm` is provided.
- For production API mode, set `PERSONAL_AI_CONFIG=config.production.yaml`.
- For real API validation, set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and run `python -m src.cli doctor-llm --call-api`.
- Run `.\run_production_check.ps1 -CallApi` before tagging a production release.
- If no API key is available in CI, run `.\run_production_check.ps1 -AllowMissingSecrets` as a wiring check.
- Reindex after changing embedding providers or vector-store backends.
- Review `SECURITY.md`.
- Verify GitHub Actions CI passes.
