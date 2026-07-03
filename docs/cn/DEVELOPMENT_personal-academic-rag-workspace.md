# 开发文档：personal-academic-rag-workspace

## 核心架构

```text
ingestion -> chunking -> indexing -> retrieval -> reranking -> grounding -> generation
```

## 关键模块

- `src/ingestion/`：PDF、docx、pptx、md、txt 解析。
- `src/chunking/`：按 chunk_size/chunk_overlap 切块，保留页码、段落、标题。
- `src/indexing/`：Chroma/JSON fallback 向量库，BM25 关键词索引。
- `src/retrieval/`：keyword、semantic、hybrid retriever。
- `src/retrieval/reranker.py`：规则重排器。
- `src/grounding/`：引用构造、置信度、证据不足判断。
- `src/generation/`：统一 LLM/Embedding 接口，mock 和 OpenAI-compatible 实现。
- `src/academic/`：论文元信息、章节识别、阅读笔记、综述表格。

## 为什么 RAG 不需要训练

标准 RAG 不训练 LLM，而是构建检索增强链路：

1. 文档解析。
2. 切块。
3. 生成 embedding。
4. 写入向量库。
5. BM25 + vector 混合召回。
6. rerank。
7. 构造 evidence context。
8. LLM 基于 evidence 生成答案。
9. 引用和置信度校验。

## 生产化关键点

- 真实 API 后端通过 `config.production.yaml` 切换。
- API key 从环境变量读取，不写死。
- `doctor-config` 验证配置、目录、依赖、key。
- `doctor-llm --call-api` 验证真实 LLM 和 embedding endpoint。
- Chroma 不可用时使用 JSON fallback，但生产建议安装 Chroma。
- 切换 embedding 模型后必须重建索引。

## 面试可讲点

- 为什么 hybrid search 比单一 vector search 更稳。
- 为什么 reranker 与 retriever 分层。
- 如何做 citation grounding。
- 如何判断 evidence insufficient。
- 为什么 mock backend 对离线测试很重要。
- 如何扩展 SentenceTransformers、Ollama、cross-encoder reranker。

## 扩展路线

- 加入本地 embedding 模型。
- 加入 cross-encoder reranker。
- 加入更细粒度 PDF layout parser。
- 建立更系统的 RAG eval dataset。
