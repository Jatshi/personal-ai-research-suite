from __future__ import annotations

import streamlit as st

from src.config.config_loader import load_config
from src.evaluation.rag_evaluator import eval_rag

st.title("Evaluation")
dataset = st.text_input("Dataset", "./examples/sample_eval/rag_eval.jsonl")
if st.button("Run RAG Eval"):
    st.json(eval_rag(load_config(), dataset, "./data/exports/eval/rag_eval_report.md"))

