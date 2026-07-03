from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.config_loader import load_config
from src.llm.providers import build_llm_client
from src.tools.default_registry import build_registry
from src.tools.planner_tools import run_agent_plan


st.title("Work Assistant Agent")
config = load_config(ROOT / "config.yaml")
registry = build_registry(config)
todo = st.text_input("Todo path", "todo.md")
goal = st.text_input("Goal", "完成个人 RAG 项目第一阶段")

if st.button("Read todo"):
    st.json(registry.call("read_todo", {"path": str(ROOT / "workspace" / todo)}).output)
if st.button("Generate task breakdown"):
    st.markdown(registry.call("generate_todo_list", {"goal": goal}).output)
use_llm_planner = st.checkbox("Use LLM planner", value=False)
if st.button("Plan agent workflow"):
    llm = build_llm_client(config) if use_llm_planner else None
    st.json(run_agent_plan(goal, registry, execute=False, confirmed=False, llm=llm, use_llm=use_llm_planner))
planner_confirm = st.checkbox("Confirm planner execution")
if st.button("Execute planned workflow"):
    llm = build_llm_client(config) if use_llm_planner else None
    st.json(run_agent_plan(goal, registry, execute=True, confirmed=planner_confirm, llm=llm, use_llm=use_llm_planner))
if st.button("Generate daily report"):
    st.markdown(registry.call("generate_daily_report", {"todo_path": str(ROOT / "workspace" / todo)}).output)
if st.button("Generate weekly report"):
    st.markdown(registry.call("generate_weekly_report", {"todo_path": str(ROOT / "workspace" / todo)}).output)

st.subheader("Email Draft")
recipient = st.text_input("Recipient", "Professor")
email_goal = st.text_input("Email goal", "汇报博士论文收尾进展")
key_points = st.text_area("Key points", "完成图表编号检查；正在整理参考文献；计划明天提交修改清单。")
if st.button("Generate email draft"):
    st.text(registry.call("generate_email_draft", {"recipient": recipient, "goal": email_goal, "key_points": key_points}).output)
