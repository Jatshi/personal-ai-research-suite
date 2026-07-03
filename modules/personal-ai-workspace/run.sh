#!/usr/bin/env bash
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_notes --collection notes
python -m src.cli search --query "RAG 是什么？" --mode hybrid --top-k 5

