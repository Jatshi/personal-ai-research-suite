# 使用文档：personal-academic-rag-workspace

## 定位

这是个人学术知识库 RAG 系统，适合管理博士论文、论文笔记、PDF 文献、会议记录、简历和项目材料。

## 安装

```powershell
cd modules\personal-academic-rag-workspace
pip install -r requirements.txt
```

## Mock 模式

不需要 API key：

```powershell
python -m src.cli ingest --path ./examples/sample_docs --collection personal
python -m src.cli ingest --path ./examples/sample_papers --collection academic
python -m src.cli search --query "RAG 是什么？" --mode hybrid --top-k 5
python -m src.cli ask --query "请总结示例论文的方法。" --collection academic
```

## 真实 LLM API 模式

```powershell
$env:PERSONAL_ACADEMIC_RAG_CONFIG="config.production.yaml"
$env:OPENAI_API_KEY="sk-..."
python -m src.cli doctor-config
python -m src.cli doctor-llm --call-api
```

切换 embedding 后需要重新导入或重建索引。

## 常用命令

```powershell
python -m src.cli ingest --path "D:\your_docs" --collection academic --doc-type paper
python -m src.cli search --query "复杂声学场景有哪些方法？" --mode hybrid --top-k 8
python -m src.cli ask --query "请总结这些材料中的创新点" --collection academic
python -m src.cli export-notes --collection academic --output ./data/exports/notes.md
python -m src.cli eval --dataset ./examples/eval/rag_eval.jsonl --output ./data/exports/rag_eval_report.md
```

## UI

```powershell
streamlit run app/streamlit_app.py
```

页面包括 Documents、Search、Ask、Academic、Settings。

## 输出如何解读

- `score`：融合后的检索分数。
- `bm25_score`：关键词匹配分数。
- `vector_score`：语义向量相似度。
- `confidence`：启发式证据置信度。
- `chunk_id`：可回溯到原文 chunk 的唯一 ID。

## 注意事项

- 不要提交 `.env`。
- 真实 API 模式下，embedding 维度变化后必须重建索引。
- 如果证据不足，系统应该拒答，而不是编造。
