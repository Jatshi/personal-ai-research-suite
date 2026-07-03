# Usage: personal-agent-workspace

## Purpose

This module is a local personal Agent workbench, not a simple chatbot. It uses tool calling to organize files, check thesis structure, read papers, generate reports, and plan tasks. Risky file operations require dry-run and human confirmation.

## Install

```powershell
cd modules\personal-agent-workspace
pip install -r requirements.txt
```

## Common Commands

```powershell
python -m src.cli scan-files --path messy_files
python -m src.cli organize-files --path messy_files --dry-run
python -m src.cli execute-organize-plan --path messy_files
python -m src.cli check-thesis --path thesis_sample/thesis.md
python -m src.cli read-papers --path papers --output ./data/exports/paper_notes
python -m src.cli assistant --goal "finish phase one of my personal RAG project"
python -m src.cli daily-report --todo ./workspace/todo.md
python -m src.cli weekly-report --todo ./workspace/todo.md
python -m src.cli show-logs
```

## Real LLM Planner

Set `llm.backend` to `openai` or `openai-compatible` in `config.yaml`, set `OPENAI_API_KEY`, then run:

```powershell
python -m src.cli plan --goal "scan and organize files path=messy_files" --llm-planner
```

Real write operations require explicit confirmation:

```powershell
python -m src.cli plan --goal "organize files path=messy_files" --llm-planner --execute --yes
```

## Streamlit UI

```powershell
streamlit run app/streamlit_app.py
```

Pages: Home, File Organizer, Thesis Finishing, Paper Reading, Work Assistant, Logs, Settings.

## Safety Rules

- Scan, read, and summarize are low-risk.
- Rename, move, delete, and write todo are high-risk.
- High-risk tools default to dry-run.
- Real execution requires `--execute --yes` or UI approval.
- File operations are written to audit logs and rollback records.

## Typical Use Cases

- Scan a messy folder and generate summaries, categories, and rename suggestions.
- Check thesis chapter, figure, table, equation, and bibliography numbering.
- Batch-read papers and generate one-page Markdown notes.
- Generate daily reports, weekly reports, and email drafts from todo and notes.
