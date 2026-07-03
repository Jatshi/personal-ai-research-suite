# Demo Recording Guide

This guide explains how to produce a professional walkthrough for ScholarMind AgentOS.

## Do You Need an API Key?

No, not for a UI demo.

The repository includes mock/offline mode, example documents, and generated demo assets. This is enough to record:

- the GitHub README walkthrough
- Streamlit navigation
- document ingestion
- search and ask flow
- agent workflow screens
- dry-run and audit-log behavior

You need a real API key only if the demo must show real LLM generation quality instead of mock responses.

## Recommended Demo Versions

### 1. Public GitHub Demo

Use mock mode. This is safer for a public repository because it does not reveal:

- private API keys
- private thesis files
- personal documents
- real meeting notes
- unpublished paper content

The README uses `assets/demo/scholarmind-demo.gif` because GIF files render directly on GitHub.

### 2. Real LLM Product Demo

Use this version for interviews or private portfolio presentations.

Create `.env` from `.env.example`:

```powershell
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Then switch the relevant module config from mock mode to OpenAI-compatible mode.

## Suggested Recording Script

### Scene 1: Repository Landing Page

Show:

- project name and badges
- animated demo
- module table
- architecture diagram
- documentation links

Narration:

> ScholarMind AgentOS is a local-first research AI workspace that combines academic RAG, safe AI agents, a personal AI OS, and an MCP-style tool bridge.

### Scene 2: Academic RAG

Run:

```powershell
cd modules\personal-academic-rag-workspace
python -m src.cli ingest --path .\examples\sample_docs --collection personal
python -m src.cli ask --query "请总结这个知识库中的主要主题。" --collection personal
streamlit run app\streamlit_app.py
```

Show:

- documents
- chunks
- hybrid search
- cited answers
- confidence score

### Scene 3: Safe Agent Workspace

Run:

```powershell
cd modules\personal-agent-workspace
python -m src.cli scan-files --path .\examples\messy_files
python -m src.cli organize-files --path .\examples\messy_files --dry-run
streamlit run app\streamlit_app.py
```

Show:

- file inventory
- rename/category suggestions
- dry-run operation plan
- approval requirement
- audit logs

### Scene 4: Paper Reading Workflow

Run:

```powershell
cd modules\personal-agent-workspace
python -m src.cli read-papers --path .\examples\papers --output .\data\exports\paper_notes
```

Show:

- generated reading notes
- literature review table
- multi-agent workflow log

### Scene 5: MCP-style Tool Bridge

Show:

- local tools exposed as structured tool calls
- RAG/search/filesystem/code capabilities
- external-client integration path

## README Media Notes

GitHub README supports:

- Markdown images: `![alt](path/to/image.png)`
- HTML image tags: `<img src="..." width="90%">`
- Shields.io badges: `https://img.shields.io/badge/...`
- Mermaid diagrams in fenced code blocks
- GIF files directly embedded in Markdown

GitHub does not reliably render local `.mp4` files inline in all README contexts. For public repositories, use GIF for inline demos and link to MP4 if needed.

## Current Demo Assets

- `assets/brand/scholarmind-hero.svg`
- `assets/demo/scholarmind-demo.gif`
- `assets/demo/scholarmind-demo-poster.png`

