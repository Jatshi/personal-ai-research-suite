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
config["app"]["workspace_dir"] = st.text_input("workspace_dir", config["app"]["workspace_dir"])
config["app"]["mock_mode"] = st.checkbox("mock_mode", bool(config["app"]["mock_mode"]))
config["llm"]["backend"] = st.text_input("LLM backend", config["llm"]["backend"])
config["llm"]["model_name"] = st.text_input("LLM model", config["llm"].get("model_name", "mock-agent-llm"))
config["llm"]["api_key_env"] = st.text_input("API key env var", config["llm"].get("api_key_env", "OPENAI_API_KEY"))
config["llm"]["base_url"] = st.text_input("OpenAI-compatible base_url", config["llm"].get("base_url") or "")
config["llm"]["timeout"] = st.number_input("LLM timeout seconds", min_value=5, max_value=300, value=int(config["llm"].get("timeout", 60)))
config["safety"]["require_confirmation_for_write"] = st.checkbox("Require confirmation for write", bool(config["safety"]["require_confirmation_for_write"]))
config["safety"]["allow_delete"] = st.checkbox("Allow delete", bool(config["safety"]["allow_delete"]))
if st.button("Save"):
    save_config(config, ROOT / "config.yaml")
    st.success("Saved")
st.code(yaml.safe_dump({k: v for k, v in config.items() if not k.startswith("_")}, allow_unicode=True, sort_keys=False), language="yaml")
