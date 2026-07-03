# Usage: personal-ai-workspace

## Purpose

This module is the integrated Personal AI OS: a local-first RAG + Agent + API + MCP-like tool workbench. It is the main application layer of the suite.

## Install

```powershell
cd modules\personal-ai-workspace
pip install -r requirements.txt
pip install -r requirements-production.txt
pip install -e ".[dev]"
```

## Mock Mode

```powershell
python -m src.cli ingest --path ./examples/docs --collection personal
python -m src.cli search --query "RAG" --mode hybrid --top-k 5
python -m src.cli ask --query "What is this workspace about?"
python -m src.cli agent --goal "generate a weekly report from notes and todo"
python -m src.cli doctor-config
python -m src.cli doctor-llm
```

## Real API Mode

```powershell
$env:PERSONAL_AI_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
$env:PERSONAL_AI_API_TOKEN="your-api-token"
python -m src.cli doctor-config
python -m src.cli doctor-llm --call-api
```

One-command production check:

```powershell
.\run_production_check.ps1 -CallApi
```

Without a real key, verify local production wiring only:

```powershell
.\run_production_check.ps1 -AllowMissingSecrets
```

## FastAPI

```powershell
.\run_api.ps1
```

Common endpoints:

- `GET /health`
- `POST /rag/search`
- `POST /rag/ask`
- `POST /agent/run`
- `POST /kb/ingest`
- `GET /llm/doctor`

Production config enables token-based API protection.

## Streamlit

```powershell
.\run_streamlit.ps1
```

## Evaluation

```powershell
python -m src.cli eval-rag --dataset ./examples/eval/rag_eval.jsonl
python -m src.cli eval-agent --dataset ./examples/eval/agent_eval.jsonl
```

## Use Cases

- Ingest and search local documents.
- Ask grounded RAG questions with citations.
- Run Agent tool planning.
- Generate daily/weekly reports and reading lists.
- Serve FastAPI endpoints to other apps.
- Act as the real RAG backend for `local-mcp-toolkit`.
