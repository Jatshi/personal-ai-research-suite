from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config, save_config


st.title("Settings")
config = load_config(ROOT / "config.yaml")

config["chunking"]["chunk_size"] = st.number_input("chunk_size", 200, 4000, int(config["chunking"]["chunk_size"]))
config["chunking"]["chunk_overlap"] = st.number_input("chunk_overlap", 0, 1000, int(config["chunking"]["chunk_overlap"]))
config["retrieval"]["top_k"] = st.number_input("top_k", 1, 50, int(config["retrieval"]["top_k"]))
config["retrieval"]["bm25_weight"] = st.slider("bm25_weight", 0.0, 1.0, float(config["retrieval"]["bm25_weight"]))
config["retrieval"]["vector_weight"] = st.slider("vector_weight", 0.0, 1.0, float(config["retrieval"]["vector_weight"]))
config["embedding"]["backend"] = st.text_input("embedding backend", config["embedding"]["backend"])
config["llm"]["backend"] = st.text_input("LLM backend", config["llm"]["backend"])

if st.button("Save config"):
    save_config(config, ROOT / "config.yaml")
    st.success("Saved config.yaml")

st.code(yaml.safe_dump({k: v for k, v in config.items() if not k.startswith("_")}, allow_unicode=True, sort_keys=False), language="yaml")

