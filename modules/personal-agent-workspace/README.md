# personal-agent-workspace

`personal-agent-workspace` is a local personal AI Agent workbench for file organization, thesis finishing checks, paper reading workflows, daily/weekly reports, and task planning. It is designed as a practical Agent engineering project rather than a simple chatbot: tools are registered centrally, risky file operations require dry-run and confirmation, every tool call is logged, and rename/move operations generate rollback records.

The project runs offline in mock mode by default and can also connect to a real OpenAI-compatible LLM API.

## Features

- Unified Tool Registry with `ToolSpec`, risk levels, validation, dry-run handling, confirmation checks, and JSONL logs.
- Safety layer with workspace path restriction, hidden/secret file blocking, dry-run plans, audit logs, and rollback records.
- File Organizer Agent for scanning folders, parsing documents/code/images metadata, detecting duplicates, summarizing files, suggesting categories, and proposing rename plans.
- Thesis Finishing Agent for chapter numbering, figure/table/equation numbering, bibliography references, missing sections, and Markdown/JSON reports.
- Paper Reading Multi-Agent Workflow with Reader, Method, Experiment, Critic, and Writer steps.
- Work Assistant Agent for todo parsing, task breakdowns, daily reports, weekly reports, and email drafts.
- Local RAG adapter with graceful fallback.
- Streamlit UI and CLI for all major workflows.

## Install

```powershell
cd D:\博士毕业论文\personal-agent-workspace
pip install -r requirements.txt
```

## Quick Start

```powershell
python -m src.cli scan-files --path messy_files
python -m src.cli organize-files --path messy_files --dry-run
python -m src.cli execute-organize-plan --path messy_files
python -m src.cli file-inventory
python -m src.cli plan --goal "请扫描并整理文件 path=messy_files"
python -m src.cli plan --goal "请扫描并整理文件 path=messy_files" --llm-planner
python -m src.cli check-thesis --path thesis_sample/thesis.md
python -m src.cli read-papers --path papers --output ./data/exports/paper_notes
python -m src.cli assistant --goal "完成个人 RAG 项目第一阶段"
python -m src.cli daily-report --todo ./workspace/todo.md
python -m src.cli weekly-report --todo ./workspace/todo.md
python -m src.cli show-logs
```

Real execution of risky batch operations requires explicit confirmation:

```powershell
python -m src.cli execute-organize-plan --path messy_files --execute --yes
python -m src.cli rollback-latest --execute --yes
```

## Streamlit UI

```powershell
streamlit run app/streamlit_app.py
```

Pages: Home, File Organizer, Thesis Finishing, Paper Reading, Work Assistant, Logs, Settings.

## Real LLM API

Set the API key and configure `llm.backend` in `config.yaml`:

```powershell
$env:OPENAI_API_KEY="sk-..."
python -m src.cli plan --goal "请扫描并整理文件 path=messy_files" --llm-planner
```

For OpenAI-compatible gateways, set `base_url` in config or `OPENAI_BASE_URL` in the environment.

## Safety Model

- Read-only tools can run directly.
- Write, move, rename, delete, and todo-writing tools are high risk.
- High-risk tools default to dry-run.
- Real execution requires explicit confirmation.
- Tool calls and file operations are logged.
- Move/rename operations create rollback records.

## Tests

```powershell
pytest -q
```

## Resume Summary

Designed and implemented `personal-agent-workspace`, a local AI Agent workbench for file management, thesis finishing, paper reading, and work reporting. The system supports Tool Calling, Human-in-the-loop approval, dry-run execution, audit logs, rollback records, multi-agent paper reading workflows, and an extensible OpenAI-compatible LLM interface.
