# 使用文档：personal-ai-workspace

## 定位

这是综合型 Personal AI OS：一个本地优先的 RAG + Agent + API + MCP-like 工具工作台。它适合作为四项目组合后的主应用。

## 安装

```powershell
cd modules\personal-ai-workspace
pip install -r requirements.txt
pip install -r requirements-production.txt
pip install -e ".[dev]"
```

## Mock 模式

```powershell
python -m src.cli ingest --path ./examples/docs --collection personal
python -m src.cli search --query "RAG" --mode hybrid --top-k 5
python -m src.cli ask --query "What is this workspace about?"
python -m src.cli agent --goal "根据本周笔记和 todo 生成周报"
python -m src.cli doctor-config
python -m src.cli doctor-llm
```

## 真实 API 模式

```powershell
$env:PERSONAL_AI_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
$env:PERSONAL_AI_API_TOKEN="your-api-token"
python -m src.cli doctor-config
python -m src.cli doctor-llm --call-api
```

一键生产自检：

```powershell
.\run_production_check.ps1 -CallApi
```

没有真实 key 时可以只检查生产配置和本地连线：

```powershell
.\run_production_check.ps1 -AllowMissingSecrets
```

## FastAPI

```powershell
.\run_api.ps1
```

常用接口：

- `GET /health`
- `POST /rag/search`
- `POST /rag/ask`
- `POST /agent/run`
- `POST /kb/ingest`
- `GET /llm/doctor`

生产配置下 API token 会保护接口。

## Streamlit

```powershell
.\run_streamlit.ps1
```

## 评估

```powershell
python -m src.cli eval-rag --dataset ./examples/eval/rag_eval.jsonl
python -m src.cli eval-agent --dataset ./examples/eval/agent_eval.jsonl
```

## 适合做什么

- 统一导入和检索本地文档。
- 进行可引用 RAG 问答。
- 运行 Agent tool planner。
- 生成日报、周报、阅读清单。
- 提供 FastAPI 给前端或其他服务调用。
- 作为 MCP toolkit 的下游真实 RAG 后端。
