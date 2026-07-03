from __future__ import annotations

import streamlit as st
import yaml

from src.config.config_loader import load_config, save_config
from src.cli import doctor_llm

config = load_config()
st.title("Settings")
st.subheader("LLM / Embedding Backend")
st.write(
    {
        "llm_backend": config.get("llm", {}).get("backend"),
        "llm_model": config.get("llm", {}).get("model_name"),
        "embedding_backend": config.get("embedding", {}).get("backend"),
        "embedding_model": config.get("embedding", {}).get("model_name"),
    }
)
if st.button("Check LLM Config"):
    st.json(doctor_llm(config, call_api=False))

text = st.text_area("config.yaml", yaml.safe_dump({k: v for k, v in config.items() if k != "_project_root"}, allow_unicode=True, sort_keys=False), height=520)
if st.button("Save Config"):
    save_config(yaml.safe_load(text))
    st.success("Saved")
