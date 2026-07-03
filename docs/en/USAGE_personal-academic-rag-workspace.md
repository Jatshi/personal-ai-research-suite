# Usage: personal-academic-rag-workspace

## Purpose

This module is the academic and personal knowledge-base RAG system. It is designed for thesis materials, paper notes, PDF literature, meeting notes, resumes, and project documents.

## Install

```powershell
cd modules\personal-academic-rag-workspace
pip install -r requirements.txt
```

## Mock Mode

No API key is required:

```powershell
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_papers --collection academic
python -m src.cli search --query "What is RAG?" --mode hybrid --top-k 5
python -m src.cli ask --query "Summarize the method of the sample paper." --collection academic
```

## Real LLM API Mode

```powershell
$env:PERSONAL_ACADEMIC_RAG_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
python -m src.cli doctor-config
python -m src.cli doctor-llm --call-api
```

Rebuild the index after changing embedding models.

## Common Commands

```powershell
python -m src.cli ingest --path "D:\your_docs" --collection academic --doc-type paper
python -m src.cli search --query "methods for complex acoustic scenes" --mode hybrid --top-k 8
python -m src.cli ask --query "summarize the main contributions" --collection academic
python -m src.cli export-notes --collection academic --output ./data/exports/notes.md
python -m src.cli eval --dataset ./examples/eval/rag_eval.jsonl --output ./data/exports/rag_eval_report.md
```

## UI

```powershell
streamlit run app/streamlit_app.py
```

Pages: Documents, Search, Ask, Academic, Settings.

## How To Read Results

- `score`: fused retrieval score.
- `bm25_score`: keyword matching score.
- `vector_score`: semantic similarity score.
- `confidence`: heuristic evidence confidence.
- `chunk_id`: traceable source chunk ID.

## Notes

- Never commit `.env`.
- Reindex after changing embedding models.
- The system should refuse unsupported questions instead of hallucinating.
