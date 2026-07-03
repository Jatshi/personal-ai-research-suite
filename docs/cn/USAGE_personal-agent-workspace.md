# 使用文档：personal-agent-workspace

## 定位

这是本地个人 Agent 工作台，不是普通聊天机器人。它用工具调用完成文件整理、博士论文检查、论文阅读、日报周报、任务规划，并对危险文件操作执行 dry-run 和人工确认。

## 安装

```powershell
cd modules\personal-agent-workspace
pip install -r requirements.txt
```

## 常用命令

```powershell
python -m src.cli scan-files --path messy_files
python -m src.cli organize-files --path messy_files --dry-run
python -m src.cli execute-organize-plan --path messy_files
python -m src.cli check-thesis --path thesis_sample/thesis.md
python -m src.cli read-papers --path papers --output ./data/exports/paper_notes
python -m src.cli assistant --goal "完成个人 RAG 项目第一阶段"
python -m src.cli daily-report --todo ./workspace/todo.md
python -m src.cli weekly-report --todo ./workspace/todo.md
python -m src.cli show-logs
```

## 真实 LLM Planner

在 `config.yaml` 中把 `llm.backend` 改为 `openai` 或 `openai-compatible`，设置 `OPENAI_API_KEY` 后运行：

```powershell
python -m src.cli plan --goal "请扫描并整理文件 path=messy_files" --llm-planner
```

执行真实写操作必须显式确认：

```powershell
python -m src.cli plan --goal "请整理文件 path=messy_files" --llm-planner --execute --yes
```

## Streamlit UI

```powershell
streamlit run app/streamlit_app.py
```

页面包括 Home、File Organizer、Thesis Finishing、Paper Reading、Work Assistant、Logs、Settings。

## 安全原则

- 扫描、读取、摘要属于低风险。
- rename、move、delete、write todo 属于高风险。
- 高风险工具默认 dry-run。
- 真实执行需要 `--execute --yes` 或 UI 中人工确认。
- 文件操作写入 audit log 和 rollback 记录。

## 典型使用场景

- 扫描混乱文件夹，生成摘要、分类、重命名建议。
- 检查博士论文图表编号、章节编号、参考文献。
- 批量阅读论文并生成一页式 Markdown note。
- 根据 todo 和笔记生成日报、周报和邮件草稿。
