from __future__ import annotations

import streamlit as st

from src.agents.personal_assistant_agent import PersonalAssistantAgent
from src.config.config_loader import load_config
from src.tools.default_registry import build_registry

st.title("Agent Workspace")
goal = st.text_area("Goal", "根据本周笔记和 todo 生成周报")
if st.button("Run Agent"):
    st.json(PersonalAssistantAgent(build_registry(load_config())).run(goal))

