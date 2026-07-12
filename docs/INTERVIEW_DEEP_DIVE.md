# ScholarMind AgentOS 面试级技术深度手册

> 本文档面向面试准备，覆盖每个模块的核心实现原理、设计决策和常见面试问答。

---

## 目录

- [第一部分：RAG 全链路（最高频考点）](#第一部分rag-全链路最高频考点)
  - [1.1 文档解析层 Ingestion](#11-文档解析层-ingestion)
  - [1.2 切块层 Chunking](#12-切块层-chunking)
  - [1.3 索引层 Indexing](#13-索引层-indexing)
  - [1.4 检索层 Retrieval](#14-检索层-retrieval)
  - [1.5 重排层 Reranking](#15-重排层-reranking)
  - [1.6 证据与引用 Grounding](#16-证据与引用-grounding)
  - [1.7 生成层 Generation](#17-生成层-generation)
  - [1.8 RAG 评估](#18-rag-评估)
  - [1.9 高级 RAG 编排](#19-高级-rag-编排)
- [第二部分：Agent 系统](#第二部分agent-系统)
  - [2.1 Tool Registry 设计](#21-tool-registry-设计)
  - [2.2 安全机制 Safety](#22-安全机制-safety)
  - [2.3 Agent 规划与执行](#23-agent-规划与执行)
  - [2.4 多 Agent 论文阅读工作流](#24-多-agent-论文阅读工作流)
  - [2.5 文件整理 Agent](#25-文件整理-agent)
  - [2.6 博士论文检查 Agent](#26-博士论文检查-agent)
  - [2.7 Agent 评估](#27-agent-评估)
  - [2.8 ReAct、恢复与记忆](#28-react恢复与记忆)
- [第三部分：MCP 工具协议层](#第三部分mcp-工具协议层)
  - [3.1 MCP 与普通 HTTP API 的区别](#31-mcp-与普通-http-api-的区别)
  - [3.2 ToolSpec 设计](#32-toolspec-设计)
  - [3.3 RAG Bridge 与 Adapter 模式](#33-rag-bridge-与-adapter-模式)
  - [3.4 MCP Server 运行](#34-mcp-server-运行)
  - [3.5 MCP Server 运行](#35-mcp-server-运行)
  - [3.6 Filesystem Safety](#36-filesystem-safety)
- [第四部分：集成层 Personal AI Workspace](#第四部分集成层-personal-ai-workspace)
  - [4.1 Agent Harness 执行流程](#41-agent-harness-执行流程)
  - [4.2 FastAPI 设计](#42-fastapi-设计)
  - [4.3 可观测性 Observability](#43-可观测性-observability)
  - [4.4 评估体系](#44-评估体系)
- [第五部分：工程化与生产设计](#第五部分工程化与生产设计)
  - [5.1 配置管理](#51-配置管理)
  - [5.2 配置管理](#52-配置管理)
  - [5.3 诊断命令 Doctor](#53-诊断命令-doctor)
  - [5.4 Monorepo 与 Bounded Context](#54-monorepo-与-bounded-context)
- [第六部分：面试高频 Q&A](#第六部分面试高频-qa)
- [第七部分：GraphRAG](#第七部分graphrag)
- [第八部分：多 Agent 协作](#第八部分多-agent-协作)
- [第九部分：评估体系](#第九部分评估体系)

---

## 第一部分：RAG 全链路（最高频考点）

### 1.1 文档解析层 Ingestion

**代码位置**：`personal-academic-rag-workspace/src/ingestion/`

**实现原理**：

采用**策略模式**，通过一个 `LOADERS` 字典映射文件后缀到对应的解析函数：

```python
LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".pptx": load_pptx,
    ".md": load_markdown,
    ".txt": load_txt,
}
```

`load_document()` 统一入口函数做三件事：
1. 根据后缀选择 loader
2. 提取文件 stat 信息（修改时间等）构造 base_metadata
3. 调用对应 loader 返回 `list[DocumentSegment]`

每个 loader 返回的是 `DocumentSegment(text, metadata)` 列表，metadata 包含 filename、source_path、file_type、collection、tags、date 等字段。

**面试要点**：
- Q：为什么不用一个通用 parser？A：不同格式解析库完全不同（PyMuPDF 处理 PDF、python-docx 处理 Word），强行统一反而增加复杂度。策略模式让新增格式只需加一个 loader 函数。
- Q：metadata 为什么在这个阶段就注入？A：因为后续切块和索引都需要追踪来源。chunk 级别的元信息（页码、段落）从这里继承。

---

### 1.2 切块层 Chunking

**代码位置**：`personal-academic-rag-workspace/src/chunking/chunker.py`

**实现原理**：

`TextChunker` 采用**滑动窗口 + 重叠**策略：

```python
class TextChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120):
```

核心算法是逐段累积文本，当 buffer 超过 `chunk_size` 时切出一个 chunk，保留末尾 `chunk_overlap` 字符作为下一个 chunk 的开头：

```python
if len(buffer) + len(text) + 1 <= self.chunk_size:
    buffer = f"{buffer}\n{text}".strip()  # 继续累积
else:
    chunks.append(self._make_chunk(...))
    overlap = buffer[-self.chunk_overlap:]  # 保留重叠区
    buffer = f"{overlap}\n{text}".strip()
```

还有一个**安全溢出处理**：如果单段文本超过 `chunk_size * 1.5`，会强制按 chunk_size 切割，防止某个巨大段落导致 chunk 失控。

**ID 生成**（`metadata.py`）：
- `doc_id` = SHA1(collection:path)[:16]
- `chunk_id` = `{doc_id}-{index:04d}-{SHA1(doc_id:index:text[:200])[:12]}`

这样每个 chunk 都有全局唯一、确定性、可回溯的 ID。

**面试要点**：
- Q：chunk_size 和 chunk_overlap 怎么选？A：学术论文一般 800-1000 字符合适，overlap 10-15% 防止语义在边界断裂。太小说明不完整，太大检索噪声多。
- Q：为什么不用递归字符切分（如 LangChain 的 RecursiveCharacterTextSplitter）？A：当前实现按段落边界切，保持语义完整性。递归切分在段落内部强制断行会破坏学术文本的结构。
- Q：chunk_id 为什么包含文本哈希？A：保证同一内容的 ID 稳定，支持幂等 upsert（相同内容不会重复索引）。

---

### 1.3 索引层 Indexing

**代码位置**：`personal-academic-rag-workspace/src/indexing/`

#### 1.3.1 向量索引 VectorStore

**双后端设计**：

```python
class VectorStore:
    def __init__(self, persist_dir, embedding_client, collection_name):
        # 优先尝试 Chroma
        try:
            import chromadb
            self._client = chromadb.PersistentClient(...)
            self._collection = self._client.get_or_create_collection(collection_name)
            self.backend = "chroma"
        except Exception:
            self.backend = "json"  # fallback
```

- **Chroma 模式**：`PersistentClient` 持久化到磁盘，支持 `upsert`、`query`、`delete`
- **JSON 备用**：所有 chunk 和 embedding 存在一个 JSON 文件中，检索时遍历计算余弦相似度

搜索时向量分数转换：`score = max(0.0, 1.0 - distance)`（Chroma 默认用 L2 距离）

#### 1.3.2 BM25 索引 BM25Store

**手写 BM25 实现**，不依赖第三方库：

```python
class BM25Store:
    def __init__(self, chunks, k1=1.5, b=0.75):
```

核心公式（标准 BM25）：

```
IDF(qi) = log(1 + (N - df(qi) + 0.5) / (df(qi) + 0.5))
Score = IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
```

- `k1=1.5`：词频饱和参数，控制 tf 的非线性增长
- `b=0.75`：文档长度归一化参数，较长文档的权重会被适度降低
- 最后做了**归一化**：`score / max_score`，使分数在 [0, 1] 区间

**分词函数** `tokenize()`（`text_utils.py`）：
- 拉丁文：正则提取 `[A-Za-z0-9_]+`
- 中文：提取连续 CJK 字符，生成 2-gram 和 3-gram
- 中英翻译提示：内置 `_ZH_QUERY_HINTS` 字典，如 "方法" -> ["method", "methods"]

**面试要点**：
- Q：为什么手写 BM25 而不用 whoosh/jieba？A：手写让你理解 BM25 公式细节，不依赖外部搜索库。生产环境可以替换。
- Q：BM25 分数为什么要归一化到 [0,1]？A：因为后续 hybrid search 要和向量分数做加权融合，两个分数必须在同一量级。
- Q：中文分词为什么用 n-gram 而不用 jieba？A：n-gram 不需要词典就能分词。对学术文本，2-gram 和 3-gram 的召回已经足够好。

---

### 1.4 检索层 Retrieval

**代码位置**：`personal-academic-rag-workspace/src/retrieval/`

#### 三种检索模式

| 模式 | 实现 | 适用场景 |
|---|---|---|
| `keyword` | BM25Store 直接搜 | 精确术语匹配（人名、方法名、公式编号） |
| `semantic` | VectorStore 直接搜 | 语义相似查询（"这篇论文的创新点是什么"） |
| `hybrid` | 两者都搜，融合分数 | **默认模式**，综合优势 |

#### HybridRetriever 融合策略

```python
class HybridRetriever:
    def __init__(self, keyword_retriever, semantic_retriever, bm25_weight=0.4, vector_weight=0.6):
```

**关键实现细节**：

1. **扩大召回**：hybrid 模式下，每种检索器各召回 `top_k * 3`（至少 10 条）
2. **去重合并**：以 `chunk_id` 为 key 合并两个检索器的结果，同一 chunk 保留两个分数
3. **加权融合**：`score = 0.4 * bm25_score + 0.6 * vector_score`
4. **统一重排**：合并后送入 reranker

```python
for r in self.keyword_retriever.search(query, k, filters):
    merged[r.chunk.chunk_id] = r
for r in self.semantic_retriever.search(query, k, filters):
    if r.chunk.chunk_id in merged:
        merged[r.chunk.chunk_id].vector_score = r.vector_score  # 补充向量分
    else:
        merged[r.chunk.chunk_id] = r
for r in merged.values():
    r.score = self.bm25_weight * r.bm25_score + self.vector_weight * r.vector_score
```

**面试要点**：
- Q：为什么 hybrid 比纯向量好？A：向量搜索擅长语义相似但会漏掉精确关键词（如专有名词、论文编号）。BM25 补了这个短板。学术场景下很多查询包含精确术语，hybrid 更稳。
- Q：权重 0.4/0.6 怎么确定的？A：向量搜索在语义理解上通常更强，给更高权重。实际可通过 eval 数据集调优。
- Q：为什么召回 3 倍？A：两种检索器的 top 结果可能有大量重叠，扩大召回保证融合后有足够的候选进入 reranker。

---

### 1.5 重排层 Reranking

**代码位置**：`personal-academic-rag-workspace/src/retrieval/reranker.py`

**规则重排器** `RuleReranker`，不依赖模型：

```python
class RuleReranker:
    def rerank(self, query, results, top_k):
        q_terms = set(tokenize(query))
        for r in results:
            # 1. 标题/文件名命中
            title_hit = 1.0 if q_terms & set(tokenize(meta_text)) else 0.0
            # 2. 关键词覆盖率
            coverage = keyword_coverage(query, r.chunk.text)
            # 3. 基础分数（取最高分）
            base = max(r.score, r.bm25_score, r.vector_score)
            # 加权融合
            r.rerank_score = 0.55 * base + 0.30 * coverage + 0.15 * title_hit
```

**三个信号**：
- **基础检索分**（55%）：hybrid 融合后的分数
- **关键词覆盖率**（30%）：query 的 token 在 chunk 中出现的比例
- **标题命中**（15%）：query 的 token 是否出现在文件名或标题中

**面试要点**：
- Q：为什么不用 cross-encoder reranker？A：当前是轻量级实现，cross-encoder 需要额外模型。规则重排不依赖外部模型，适合快速迭代。生产环境可以替换。
- Q：reranker 和 retriever 为什么分层？A：单一检索器很难同时做好召回和精排。retriever 负责广召回（recall），reranker 负责精排（precision）。分层后可以独立替换每一层。

---

### 1.6 证据与引用 Grounding

**代码位置**：`personal-academic-rag-workspace/src/grounding/`

#### 1.6.1 证据充分性检查

`evidence_checker.py`：

```python
def has_sufficient_evidence(query, results, min_confidence=0.35):
    conf = confidence_score(query, results)
    max_coverage = max(keyword_coverage(query, r.chunk.text) for r in results)
    max_score = max(max(r.score, ...) for r in results)
    return conf >= 0.35 and max_coverage >= 0.05 and max_score > 0.05, conf
```

三个条件同时满足才认为证据充分：
- 置信度 >= 0.35
- 最佳 coverage >= 0.05（至少有一个 query token 出现在证据中）
- 最佳分数 > 0.05（检索到了有意义的结果）

#### 1.6.2 置信度计算

`confidence.py`：

```python
def confidence_score(query, results):
    top = max(results[0].score, ...)
    count_factor = min(len(results) / 5, 1.0)  # 结果数量因子
    coverage = max(keyword_coverage(...) for r in results)
    if coverage <= 0:
        return min(0.2, 0.45 * min(top, 1.0))  # 无覆盖时给低分
    score = 0.45 * top + 0.25 * count_factor + 0.30 * coverage
    return clamp(score, 0.0, 1.0)
```

**三个维度**：
- **顶部分数**（45%）：最好的检索结果分数
- **结果数量**（25%）：检索到的结果越多，说明知识库对这个问题覆盖越好
- **关键词覆盖**（30%）：query 词汇在证据中的覆盖率

#### 1.6.3 引用构造

`citation_builder.py`：

```python
def build_citations(results):
    for r in results:
        page = c.metadata.get("page")
        loc = f"page {page}" if page else f"paragraph {para}" if para else "unknown location"
        citations.append(f"[{i+1}] {filename}, {loc}, chunk_id={chunk_id}")
```

每个引用包含：序号、文件名、定位（页码/段落）、chunk_id（可回溯到原文）。

**面试要点**：
- Q：为什么要做证据充分性检查？A：减少幻觉。如果知识库里没有相关内容，LLM 可能会编造答案。先检查再决定是否调用 LLM。
- Q：拒答策略是什么？A：返回固定字符串 "知识库中没有足够证据回答该问题。"，不会让 LLM 自由发挥。
- Q：confidence 三个维度的权重怎么定的？A：顶部分数最重要（检索质量），覆盖率和数量是辅助信号。可通过 eval 数据集调优。

---

### 1.7 生成层 Generation

**代码位置**：`personal-academic-rag-workspace/src/generation/`

#### 1.7.1 抽象接口

```python
class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: list[dict] | None = None) -> str: ...

class BaseEmbeddingClient(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    @abstractmethod
    def embed_query(self, query: str) -> list[float]: ...
```

所有实现类均通过统一的 `OPENAI_BASE_URL` + `OPENAI_API_KEY` 配置对接外部 API。

#### 1.7.2 OpenAI Compatible Embedding Client

```python
class OpenAICompatibleEmbeddingClient:
    def embed_texts(self, texts):
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [item.embedding for item in response.data]
```

**关键设计**：
- `base_url` 参数支持任何 OpenAI 兼容 API（包括 DeepSeek、通义千问、本地 Ollama/vLLM 等）
- API key 从环境变量读取，不硬编码
- 支持 batch embedding，提高吞吐量

#### 1.7.3 OpenAI Compatible LLM Client

```python
class OpenAICompatibleLLMClient:
    def generate(self, prompt, context):
        system = (
            "You are a grounded academic RAG assistant. "
            "Answer only from the provided evidence. "
            "If the evidence is insufficient, answer exactly: 知识库中没有足够证据回答该问题。"
            "Cite evidence with bracket numbers when making claims."
        )
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{prompt}\n\nEvidence:\n{evidence}"},
            ],
            temperature=0.2,  # 低温度减少创造性
            max_tokens=1000,
        )
```

**关键设计**：
- `base_url` 参数支持任何 OpenAI 兼容 API（包括本地 Ollama、vLLM 等）
- API key 从环境变量读取，不硬编码
- system prompt 强制 "只基于证据回答"，否则返回拒答字符串
- `temperature=0.2` 低温度让生成更确定、更忠实于证据

#### 1.7.4 AnswerGenerator 编排

```python
class AnswerGenerator:
    def answer(self, query, results):
        ok, confidence = has_sufficient_evidence(query, results, self.min_confidence)
        if not ok:
            return Answer(INSUFFICIENT_EVIDENCE_MESSAGE, [], confidence, results)
        text = self.llm.generate(ANSWER_PROMPT.format(query=query), context=context)
        citations = build_citations(results)
        return Answer(text=text + citations, citations=citations, confidence=confidence, evidence=results)
```

**编排逻辑**：先检查证据 -> 调用 LLM -> 构造引用 -> 返回完整 Answer

---

### 1.8 RAG 评估

**代码位置**：`personal-ai-workspace/src/evaluation/`

**评估数据格式**（JSONL）：
```json
{"question": "...", "expected_sources": ["file1.pdf"], "expected_keywords": ["RAG", "检索"], "should_answer": true}
```

**评估指标**（`metrics.py`）：

| 指标 | 含义 | 计算方式 |
|---|---|---|
| `retrieval_hit_rate` | 检索命中率 | expected_sources 与实际检索到文件的交集比例 |
| `source_accuracy` | 来源准确率 | 同 retrieval_hit_rate |
| `citation_presence` | 引用存在率 | 应该回答的问题中，回答是否包含引用 |
| `refusal_accuracy` | 拒答准确率 | 不该回答时是否拒答 + 该回答时是否没拒答 |
| `answer_keyword_coverage` | 答案关键词覆盖率 | 期望关键词出现在答案中的比例 |
| `average_confidence` | 平均置信度 | 所有答案的 confidence 均值 |

**面试要点**：
- Q：为什么既保留自建评估，又接入 RAGAS？A：自建评估轻量、确定、适合 CI，能精确测来源、引用和拒答；RAGAS 需要真实评审模型，但能补充 faithfulness、相关性和 context 质量。两者不是替代关系，而是“回归测试 + 生成质量审查”的双层体系。
- Q：refusal_accuracy 为什么重要？A：RAG 系统最危险的不是答错，而是不该答的时候编造。拒答准确率直接衡量系统的幻觉控制能力。

---

### 1.9 高级 RAG 编排

**代码位置**：`personal-ai-workspace/src/retrieval/`

基础 hybrid retrieval 像“去图书馆按题目找书”；高级 RAG 在它前后增加了一个
**检索调度员**：先改写问题、判断证据质量、必要时继续找关联材料，最后只把预算内的有效句子交给模型。

#### 查询改写：HyDE 与 Decomposition

`QueryRewriter` 由 `retrieval.query_rewrite` 配置驱动。

- **HyDE**（Hypothetical Document Embeddings）：先让 LLM 写一小段“假如能回答这个问题，证据大概会怎么写”，再用这段假想答案做语义检索；原问题仍用于 BM25。它像先写一张“理想书摘”，再拿书摘去书架附近找书。
- **Decomposition**：把复杂问题拆成最多 `max_subqueries` 个可独立检索的子问题，分别搜索、按 `chunk_id` 去重。它像把“比较三篇论文的方法和实验”拆成“各自方法”“各自数据集”“各自结果”。

```python
if self.mode == "hyde":
    hypothetical = self.llm.generate("Write a short hypothetical evidence passage ...")
    return [QueryVariant(query, "original"), QueryVariant(hypothetical, "hyde")]
```

面试时要强调：改写不是替换用户问题，而是**产生多个召回入口**；trace 会保留 `kind`，因此可以解释每条证据是被原问题还是子问题找到的。

#### 上下文压缩：token budget 与 extractive

检索到十段材料不代表应把十段全文都塞给模型。上下文太长会增加成本、稀释重点，还可能超过模型窗口。

- `token_budget`：按重排分从高到低装入，直到 `max_context_chars` 用完，类似登机时先装最重要的行李。
- `extractive`：从**已命中的原 chunk**中抽相关句，不重新编造摘要；每个压缩片段保留 `compressed_from_chunk_id`，所以引用仍能回到原文。

```python
item["text"] = first_sentences(text, remaining)
item["compressed_from_chunk_id"] = chunk.get("chunk_id")
```

#### CRAG 自适应路由

CRAG 在这里不是额外的神秘模型，而是根据 `confidence_score` 的三档策略：

| 路由 | 条件 | 动作 |
|---|---|---|
| `high` | 证据充分 | 直接生成有引用的答案 |
| `medium` | 有一些线索但不够稳 | 扩大 top-k 后再检索 |
| `low` | 没结果或 confidence 低于阈值 | 固定 grounded refusal，不让 LLM 猜 |

```python
if not chunks or confidence < min_confidence:
    return RouteDecision("low", confidence, "insufficient_evidence")
if confidence < min(0.75, min_confidence + 0.25):
    return RouteDecision("medium", confidence, "expand_retrieval")
return RouteDecision("high", confidence, "direct_answer")
```

这像急诊分诊：轻症直接处理，中间情况补检查，明显证据不足就不下结论。关键是低分时**拒答是产品行为，不是失败**。

#### 多跳检索

`retrieve_multi_hop()` 默认关闭且最多两跳。第一跳先找到相关 chunk，再从前几条 evidence 提取受限的英文实体/关键短语，拼成第二跳 query；结果按 `chunk_id` 合并，保留 `hop` 和 `query_variant`。

```python
expanded = expand_query_from_results(query, current)
current = search(expanded, top_k)
merged.setdefault(item["chunk_id"], {**item, "hop": hop, "query_variant": expanded})
```

适合“论文 A 用的方法在哪篇项目笔记里有实验记录”这类跨文档链路。上限必须小，否则每一跳都扩展会像在图书馆里越找越远，成本和噪声一起增长。

---

## 第二部分：Agent 系统

### 2.1 Tool Registry 设计

**代码位置**：`personal-agent-workspace/src/tools/tool_registry.py`

#### ToolSpec 数据结构

```python
@dataclass
class ToolSpec:
    name: str              # 工具名称
    description: str       # 工具描述（给 LLM planner 看的）
    input_schema: dict     # JSON Schema 风格的参数定义
    risk_level: str        # "low" | "medium" | "high"
    requires_confirmation: bool  # 是否需要人工确认
```

#### ToolRegistry 核心逻辑

```python
class ToolRegistry:
    def call(self, name, params=None, confirmed=False, dry_run=None):
        spec, fn = self._tools[name]
        # 1. 默认 dry-run 策略：medium/high 风险工具默认 dry-run
        effective_dry_run = spec.risk_level in {"medium", "high"} if dry_run is None else dry_run
        # 2. 确认检查
        if spec.requires_confirmation and not confirmed and not effective_dry_run:
            return ToolResult(False, error="Confirmation required")
        # 3. 参数校验
        self._validate_params(spec, params)
        # 4. 自动注入 dry_run/confirmed 参数
        # 5. 执行
        # 6. 审计日志
```

**参数校验**做了三件事：
1. 检查 required 字段是否都有
2. 检查是否有未知参数
3. 检查参数类型是否匹配 JSON Schema

**MCP Toolkit 的 ToolRegistry**（`local-mcp-toolkit/src/tools/registry.py`）额外做了：
- **敏感信息脱敏**：参数名含 key/token/secret 的值在日志中替换为 `***`
- **执行计时**：记录每次工具调用的 duration_ms
- **受影响文件追踪**：提取参数中含 path 的字段记录到日志

**面试要点**：
- Q：ToolSpec 为什么要包含 risk_level？A：让 Agent 在规划阶段就能判断工具的危险级别，高风险工具自动走 dry-run 路径，不需要等到执行时才发现。
- Q：为什么不用 LangChain 的 Tool 抽象？A：LangChain 的 Tool 抽象不够精细，缺少 risk_level 和 requires_confirmation。自建更贴合安全需求。
- Q：参数校验为什么手写而不用 Pydantic？A：JSON Schema 风格的校验和 MCP 协议兼容。Pydantic 也可以，但 JSON Schema 更通用。

---

### 2.2 安全机制 Safety

**代码位置**：各模块 `src/safety/`

#### 2.2.1 PathGuard（路径守卫）

两个版本的 PathGuard，功能略有不同：

**Agent 版本**（`personal-agent-workspace`）：
```python
class PathGuard:
    def validate(self, path, must_exist=False, for_write=False):
        # 1. 相对路径 -> 绝对路径（相对于 workspace_dir）
        # 2. 检查是否在 workspace 内
        if not self.allow_outside and workspace_dir not in target.parents:
            raise ValueError("Path outside workspace is blocked")
        # 3. 检查隐藏文件
        if self.block_hidden and is_hidden(relative):
            raise ValueError("Hidden files blocked")
        # 4. 检查敏感文件名
        if self.block_env and target.name.lower() in SECRET_FILE_NAMES:
            raise ValueError("Secret-like file blocked")
```

**MCP 版本**（`local-mcp-toolkit`）额外增加了：
- **符号链接逃逸检测**：`target.is_symlink()` 后 `resolve()` 检查是否仍指向 workspace 内
- **SensitiveFileGuard**：基于 `fnmatch` 的模式匹配（`.env`、`*.key`、`*.pem`、`credentials.json` 等）

```python
class SensitiveFileGuard:
    SENSITIVE_PATTERNS = [".env", "*.env", "*.key", "*.pem", "*.crt", "id_rsa", ...]
    def validate(self, path):
        for pattern in self.patterns:
            if fnmatch.fnmatch(name, pattern):
                raise PermissionError(f"Sensitive file access blocked: {name}")
```

#### 2.2.2 Dry-Run

`dry_run.py` 定义了 `OperationPlan` 数据类：
```python
@dataclass
class OperationPlan:
    operation: str       # "move_file", "rename_file", "delete_file"
    source: str
    target: str | None
    risk_level: str
    dry_run: bool = True
    details: dict | None
```

在 `file_tools.py` 中，每个写操作都遵循相同模式：
```python
def move_file(source, target, guard, audit_log, rollback, dry_run=True, confirmed=False):
    plan = {"operation": "move_file", "source": ..., "target": ..., "dry_run": dry_run}
    audit_log.write(plan | {"executed": False})
    if dry_run:
        return plan           # 只返回计划，不执行
    if not confirmed:
        raise PermissionError("move_file requires confirmation")
    shutil.move(...)           # 真正执行
    rollback.append({...})     # 记录反向操作
    audit_log.write(plan | {"executed": True})
```

#### 2.2.3 Audit Log

`JsonlAuditLog`：每条记录一行 JSON，自动添加 ISO 时间戳。适合流式写入和后续分析。

#### 2.2.4 Rollback

`RollbackStore`：和 audit_log 结构相同，但专门记录反向操作：

```python
# move A -> B 时记录
rollback.append({"operation": "move_file", "rollback": {"source": "B", "target": "A"}})
# rename A -> B 时记录
rollback.append({"operation": "rename_file", "rollback": {"source": "B_path", "new_name": "A"}})
```

`execute_latest_rollback()` 取最近一条记录，执行反向操作。

**面试要点**：
- Q：PathGuard 为什么用 `resolve()`？A：防止 `../../etc/passwd` 这种路径穿越。`resolve()` 把所有 `..` 和符号链接都展开成绝对路径，然后检查是否在 workspace 内。
- Q：dry-run 和 confirmation 是什么关系？A：dry-run 是"只展示计划不执行"，confirmation 是"用户确认后执行"。两者独立但互补：dry-run 先看计划，确认后再真正执行。
- Q：为什么不直接用 transactions（事务）？A：文件系统不支持原子事务。rollback 是文件操作层面的"补偿事务"，虽然不完美但足够实用。

---

### 2.3 Agent 规划与执行

**代码位置**：`personal-agent-workspace/src/tools/planner_tools.py`

#### 2.3.1 双模 Planner

**规则 Planner**（`plan_agent_task`）：基于关键词匹配的简单规划器：
```python
if any(token in text for token in ["整理", "organize", "rename"]):
    steps.append({"tool": "organize_files", "params": {"path": path}, "dry_run": True})
```

**LLM Planner**（`plan_agent_task_with_llm`）：
1. 把所有 ToolSpec 序列化为 JSON 传给 LLM
2. LLM 返回 JSON 格式的工具计划
3. `validate_plan()` 做严格校验：
   - 工具名必须在 registry 中存在
   - 必须参数不能缺
   - medium/high 风险工具强制 `dry_run=True`
4. 校验失败则回退到规则 planner

```python
def validate_plan(candidate, goal, registry, fallback, mode):
    specs = {spec.name: spec for spec in registry.specs()}
    for raw in raw_steps:
        if tool not in specs or tool == "plan_agent_task":
            continue                    # 过滤未知工具
        if any(key not in params for key in required):
            continue                    # 过滤参数不完整的
        if risk in {"medium", "high"}:
            dry_run = True              # 强制 dry-run
```

#### 2.3.2 Plan 执行

`run_agent_plan()`：
```python
for step in plan["steps"]:
    dry_run = bool(step.get("dry_run", False))
    if step["risk"] in {"medium", "high"}:
        dry_run = not (execute and confirmed)  # 高风险必须显式 execute+confirmed
    result = registry.call(step["tool"], step["params"], dry_run=dry_run, confirmed=confirmed)
```

#### 2.3.3 Personal AI Workspace 的 Agent

`personal_assistant_agent.py` 中的 `PersonalAssistantAgent`：
1. 调用 `build_tool_plan()` 让 LLM 生成 JSON 工具计划
2. `_sanitize_calls()` 做安全过滤（高风险工具强制 dry_run，去掉 confirm 参数）
3. 依次调用 registry 执行
4. `_finalize()` 汇总所有工具输出，生成最终报告
5. 整个过程记录到 `agent_runs.jsonl`

**面试要点**：
- Q：为什么要规则 planner + LLM planner 双模？A：规则 planner 是确定性的、零延迟的。LLM planner 更灵活但可能出错。双模保证了一致性和灵活性兼顾。
- Q：LLM 返回非法工具名怎么办？A：`validate_plan()` 会静默过滤掉所有不在 registry 中的工具名。如果过滤后为空，回退到规则 planner。这叫"防御性校验"。
- Q：为什么不直接让 LLM 执行工具？A：LLM 可能会"编造"工具调用。必须通过 registry 做白名单校验，确保只调用已注册的安全工具。

---

### 2.4 多 Agent 论文阅读工作流

**代码位置**：`personal-agent-workspace/src/tools/paper_tools.py`

#### 流程设计

```
Reader Agent -> Method Agent -> Experiment Agent -> Critic Agent -> Writer Agent
```

**实现方式**：不是真正的多进程/多线程 Agent，而是在一个函数中按步骤处理：

```python
def run_paper_reading_workflow(path, output):
    for file in files:
        paper = read_paper(file)                # Reader: 提取元信息
        state["steps"]["reader"] = {title, authors, year, keywords}

        method = paper["sections"].get("method")[:800]   # Method: 提取方法
        state["steps"]["method"] = {summary, innovation}

        exp = paper["sections"].get("experiment")[:800]  # Experiment: 提取实验
        state["steps"]["experiment"] = {summary, dataset, metrics}

        discussion = paper["sections"].get("discussion") # Critic: 分析局限
        state["steps"]["critic"] = {limitations, reproducibility}

        note = paper_note_markdown(paper, state)          # Writer: 整合笔记
```

#### 章节切分

`split_sections()` 用正则匹配 Markdown 标题，把论文内容按 section 分类：
```python
if "method" in title: current = "method"
elif "experiment" in title: current = "experiment"
elif "discussion" in title: current = "discussion"
elif "conclusion" in title: current = "conclusion"
```

#### 输出

- 每篇论文生成 `_reading_note.md`（结构化阅读笔记）
- 所有论文生成 `literature_review_table.md`（综述对比表格）

**面试要点**：
- Q：为什么叫"多 Agent"但实际是顺序函数调用？A：当前是简化实现。真正的多 Agent 需要消息队列/事件驱动架构。当前设计把角色分工（Reader/Method/Experiment/Critic/Writer）的概念保留下来，后续可以拆成独立 Agent。
- Q：为什么每个 section 截断 800 字符？A：避免传给 LLM 的上下文过长。800 字符足够保留核心信息。生产环境可调。

---

### 2.5 文件整理 Agent

**代码位置**：`personal-agent-workspace/src/tools/file_tools.py`

#### 扫描 `scan_folder`

1. 遍历目录，收集文件信息（filename、extension、size、hash、modified_time）
2. 标记临时文件（以 `~` 开头或 `.tmp`/`.bak` 后缀）
3. 标记空文件
4. **查重**：SHA256 哈希完全相同 + 文件名相似度 > 0.88（SequenceMatcher）

#### 分类建议 `suggest_file_category`

基于后缀和内容关键词的规则分类：
```python
if ext in CODE_EXTENSIONS: return "code"
if "thesis" in signals or "博士" in signals: return "dissertation"
if "paper" in signals: return "papers"
if "resume" in signals or "简历" in signals: return "job_search"
```

#### 重命名建议 `suggest_file_rename`

生成格式：`{year}_{category}_{topic}_v1{suffix}`
- year：从文件名和内容中提取
- category：来自 `suggest_file_category`
- topic：内容 top-3 关键词用下划线连接

#### 整理计划

`build_file_organization_plan` = 扫描 + 分类 + 重命名建议 + 生成 dry-run 操作列表

---

### 2.6 博士论文检查 Agent

**代码位置**：`personal-agent-workspace/src/tools/thesis_tools.py`

三项检查：

**1. 章节结构检查** `check_thesis_structure`：
- 用正则 `^(#{1,3})\s*([0-9]+(?:\.[0-9]+)*)?\s*(.+)$` 提取所有标题
- 检测重复编号
- 检测一级标题跳号
- 检测必要章节是否存在（摘要、绪论、方法、实验、参考文献、致谢）

**2. 图表公式编号检查** `check_figure_table_references`：
- 正则提取 "图 X.Y"、"表 X.Y"、"(X.Y)" 格式的编号
- 检测重复编号
- 检测编号跳号（连续性）

**3. 参考文献交叉检查** `check_bibliography_references`：
- 提取正文引用 `[N]` 和参考文献列表 `^[N] `
- 检测"正文引用了但参考文献列表没有"的情况（severity: high）
- 检测"参考文献列表有但正文没引用"的情况（severity: low）

---

### 2.7 Agent 评估

**代码位置**：`personal-ai-workspace/src/evaluation/agent_evaluator.py`

**评估指标**：

| 指标 | 含义 |
|---|---|
| `success_rate` | Agent 执行成功的比例 |
| `tool_coverage` | 实际调用工具与期望工具的交集比例 |
| `confirmation_policy_accuracy` | 期望需要确认 vs 实际需要确认的一致率 |

**确认检测**（`_requires_confirmation`）：递归遍历整个结果字典，查找 `"requires_confirmation": true` 或错误消息中的 "requires confirmation" 字符串。

---

### 2.8 ReAct、恢复与记忆

**代码位置**：`personal-ai-workspace/src/agents/react_agent.py`、`src/memory/memory_store.py`

#### ReAct 循环：Thought - Action - Observation

Planner 是“先一次性写好旅行计划再出发”；ReAct 是“走一步、看一眼导航、再决定下一步”。
在当前实现中，模型的隐式 Thought 不强制暴露，安全地落地为：**模型选择工具（Action）-> ToolRegistry 执行 -> 工具结果回填（Observation）-> 再请求模型**。

```python
response = llm.complete_with_tools(state.messages, registry.openai_tools())
result = registry.call(call.name, call.arguments)
state.messages.append({"role": "tool", "tool_call_id": call.call_id, "content": json.dumps(result)})
```

循环有三个刹车：`max_iterations`、相同工具和参数的重复调用检测、工具修复次数上限。它解决的是“必须看了搜索结果才能决定下一步”的任务；简单固定流程仍更适合 planner。

#### Function Calling 原生支持

`ToolSpec.to_openai_tool()` 将本地 schema 转成 OpenAI tools JSON Schema；
`OpenAICompatibleLLMClient.complete_with_tools()` 解析 provider 返回的标准 `tool_calls`。回填消息也严格使用官方形状：

```python
{"role": "assistant", "tool_calls": [{
    "id": call_id, "type": "function",
    "function": {"name": name, "arguments": json.dumps(arguments)}
}]}
{"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)}
```

这样 OpenAI-compatible 网关能理解调用链，工具依旧必须经过本地 Registry 的参数、风险和确认检查。LLM 只提出“想调用什么”，没有直接执行系统权限。

#### 错误恢复与降级

把 Agent 当成开车：不是一次打滑就停车，而是先尝试合理修正，但绝不能无上限重试。

1. `search_kb` 的 hybrid 检索失败时，自动尝试 `keyword`，并把 `hybrid_to_keyword` 写入恢复日志。
2. 其他工具失败时，记录 `llm_parameter_repair`，最多 `max_repair_attempts` 次，让下一轮模型依据 observation 修正参数。
3. provider 的原生 tool calling 失败时，回退到已校验的 JSON planner；如果 planner 也失败，使用规则 fallback plan。
4. 所有重试、降级和停止原因进入 `agent_recovery.jsonl`、`agent_runs.jsonl`。

面试回答重点：**降级的目标是保住安全和可解释性，不是为了硬做出一个答案。**

#### 三层记忆

| 层级 | 实现 | 比喻 |
|---|---|---|
| 短期记忆 | `state.messages` 的当前会话消息 | 你眼前正在看的便签 |
| 工作记忆 | `ReActState.steps`、审批状态、失败原因 | 正在填写的任务执行单 |
| 长期记忆 | SQLite `memories` 表，按 scope/关键词检索 | 可检索的工作日志本 |

长期记忆默认关闭；`MemoryStore.add()` 会拒绝 `api_key`、`sk-`、`.env`、password 等疑似敏感内容，且只保存裁剪后的任务结论。这样“记住偏好”不会变成“把密钥和私密文件永久存下来”。

---

## 第三部分：MCP 工具协议层

### 3.1 MCP 与普通 HTTP API 的区别

| 维度 | HTTP API | MCP (Model Context Protocol) |
|---|---|---|
| 通信方式 | 请求-响应（HTTP） | JSON-RPC over stdio 或 SSE |
| 工具发现 | 需要 API 文档 | `tools/list` 自动发现 |
| 参数约定 | OpenAPI/Swagger | JSON Schema 内嵌在工具定义中 |
| 安全边界 | 依赖 API gateway | 工具级别的 risk_level + dry-run + confirmation |
| 使用场景 | 服务间调用 | AI 模型直接调用本地能力 |

### 3.2 ToolSpec 设计

MCP 版本的 ToolSpec 比 Agent 版本多了 `output_schema` 和 `category`：

```python
@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    output_schema: dict | None   # 输出格式定义
    risk_level: str
    requires_confirmation: bool
    category: str                 # "filesystem" | "rag" | "code"
```

`category` 用于分组工具，也控制哪些 server 启用时注册哪些工具。

### 3.3 RAG Bridge 与 Adapter 模式

**代码位置**：`local-mcp-toolkit/src/rag/adapters.py`

**设计问题**：MCP toolkit 需要调用 RAG 能力，但不应该绑定某个具体 RAG 实现。

**解决方案**：Adapter 模式

```
MCP client -> ask_knowledge_base tool
           -> LocalCliRagAdapter（adapter）
           -> subprocess: python -m src.cli ask（目标 RAG 项目）
           -> 结构化 JSON 结果
```

`LocalCliRagAdapter` 实现统一的 RAG 后端接口，通过子进程调用目标 RAG 项目的 CLI 命令：

```python
class LocalCliRagAdapter(KnowledgeBaseInterface):
    def ask_knowledge_base(self, question, collection, top_k, require_citations):
        cmd = [sys.executable, "-m", "src.cli", "ask", "--query", question, ...]
        payload = self._run_json(cmd)  # subprocess.run + json.loads
        return {"question": question, "answer": payload.get("answer"), ...}

    def _run_json(self, cmd):
        env = os.environ.copy()
        if self.project_config:
            env["PERSONAL_AI_CONFIG"] = self.project_config  # 注入生产配置
        proc = subprocess.run(cmd, cwd=self.project_path, text=True, capture_output=True, timeout=90)
        return json.loads(proc.stdout.strip())
```

**关键设计**：
- `project_config` 参数允许 adapter 指定目标 RAG 项目的生产配置文件
- 通过环境变量 `PERSONAL_AI_CONFIG` 传递，不修改目标项目的文件
- 写操作（add/delete）保持 dry-run/confirm 语义

**面试要点**：
- Q：为什么用子进程而不是 Python import？A：解耦。MCP toolkit 和 RAG 项目是独立进程，可以独立部署、独立更新。子进程还有天然的隔离性（崩溃不会互相影响）。
- Q：为什么 adapter 继承 KnowledgeBaseInterface？A：接口隔离原则。`KnowledgeBaseInterface` 定义了 RAG 后端的统一接口（search/ask/list），adapter 实现相同接口。上层代码不需要知道后端是哪个具体项目。

### 3.4 官方 FastMCP SDK：Tools、Resources、Prompts

`personal-ai-workspace/src/mcp/mcp_server.py` 已迁移为官方 Python MCP SDK 的 `FastMCP`，不再把自写 JSON-lines wrapper 当作生产 server。

```python
mcp = FastMCP(config["mcp"]["server_name"])
mcp.tool(name="ask_kb")(ask_kb)

@mcp.resource("scholarmind://documents/{collection}")
def documents_resource(collection: str) -> str: ...

@mcp.prompt(name="grounded-rag-answer")
def grounded_rag_answer(question: str) -> str: ...
```

- **Tools**：只注册 `mcp.exposed_tools` 中的六个能力，且全部经过 `ToolRegistry`。
- **Resources**：`scholarmind://collections`、documents、document、recent logs，供 MCP 客户端按 URI 读取上下文。
- **Prompts**：grounded RAG、research summary、safe note writing，把常用工作流封装为可发现提示模板。

比喻：Tool 是“可以按的按钮”，Resource 是“可以翻阅的资料架”，Prompt 是“已经写好的工作说明书”。三者让客户端不只会调用函数，还能发现上下文和推荐用法。

`python -m src.cli mcp-serve` 走官方 SDK stdio；`mcp-legacy-serve` 仅用于迁移诊断。

### 3.5 MCP Server 运行

**代码位置**：`local-mcp-toolkit/src/mcp_servers/combined_server.py`

```python
def run_stdio_server(registry):
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("scholarmind")

    @mcp.tool()
    async def search_documents(query: str, top_k: int = 5):
        return registry.call("search_documents", {"query": query, "top_k": top_k})

    mcp.run()
```

使用官方 `mcp` Python SDK 的 `FastMCP` 暴露工具，自动支持 `tools/list`、`tools/call`、`resources/list` 等标准协议。

### 3.6 Filesystem Safety

MCP 版本比 Agent 版本多了：

1. **符号链接逃逸检测**：
```python
if target.is_symlink():
    resolved = target.resolve()
    if workspace_dir not in resolved.parents:
        raise PermissionError("Symlink escapes workspace")
```

2. **SensitiveFileGuard**：基于 `fnmatch` 模式匹配，覆盖 `.env`、`*.key`、`*.pem`、`*.crt`、`*.p12`、`id_rsa`、`id_ed25519`、`credentials.json`、`secrets.*`、`*.secret`、`*.token`

3. **隐藏目录拦截**：路径中任何部分以 `.` 开头都会被拦截

---

## 第四部分：集成层 Personal AI Workspace

### 4.1 Agent Harness 执行流程

```
user goal
  -> LLM tool planner 生成 JSON tool plan
  -> _sanitize_calls() 安全过滤
     - 过滤未知工具
     - 高风险工具强制 dry_run
     - 去掉 confirm 参数
  -> 依次调用 ToolRegistry 执行
  -> _finalize() 汇总报告
  -> log_event() 记录到 agent_runs.jsonl
```

`_sanitize_calls()` 是安全核心：
```python
def _sanitize_calls(calls, tools, max_steps):
    allowed = {t["name"]: t for t in tools}
    for call in calls[:max_steps]:
        if name not in allowed: continue      # 未知工具跳过
        if spec["risk_level"] in {"medium", "high"}:
            args["dry_run"] = True            # 强制 dry-run
            args.pop("confirm", None)         # 去掉确认参数
```

### 4.2 FastAPI 设计

**代码位置**：`personal-ai-workspace/src/api/fastapi_app.py`

| 接口 | 方法 | 功能 |
|---|---|---|
| `/health` | GET | 健康检查，返回 LLM/embedding 后端类型 |
| `/rag/search` | POST | 检索知识库 |
| `/rag/ask` | POST | 带引用的 RAG 问答 |
| `/agent/run` | POST | 运行 Agent |
| `/kb/ingest` | POST | 导入文档 |
| `/kb/docs` | GET | 列出文档 |
| `/kb/reindex` | POST | 重建索引 |
| `/kb/delete` | POST | 删除文档（需要 confirm=true） |
| `/llm/doctor` | GET | LLM 健康诊断 |
| `/observability/logs` | GET | 获取最近日志 |

**API 认证**：
```python
def require_api_token(authorization=None, x_api_key=None):
    if not server_cfg.get("api_auth_enabled", False): return
    expected = os.getenv(token_env)
    provided = x_api_key or _bearer_token(authorization)
    if provided != expected: raise HTTPException(401)
```

支持两种方式：`X-API-Key` header 或 `Authorization: Bearer <token>` header。

**删除文档的安全设计**：
```python
@app.post("/kb/delete")
def kb_delete(payload: DeleteDocRequest):
    plan = {..., "confirm": payload.confirm}
    if not payload.confirm:
        return {"requires_confirmation": True, "plan": plan}  # 只返回计划
    # 真正删除
```

### 4.3 可观测性 Observability

**JSONL 日志体系**（`data/logs/` 下）：

| 日志文件 | 记录内容 |
|---|---|
| `rag_queries.jsonl` | 每次检索的 query、mode、top_k、结果数 |
| `tool_calls.jsonl` | 每次工具调用的名称、参数、结果、耗时 |
| `agent_runs.jsonl` | 每次 Agent 运行的 goal、plan、步骤、结果 |
| `audit.jsonl` | 安全审计事件 |
| `errors.jsonl` | 错误事件 |

**Dashboard**：`dashboard_summary()` 从 SQLite 和 JSONL 日志中取最近 5 条记录，供 Streamlit Dashboard 展示。

### 4.4 评估体系

**RAG 评估**：见 1.8 节

**Agent 评估**：见 2.7 节

**运行方式**：
```powershell
python -m src.cli eval-rag --dataset ./examples/eval/rag_eval.jsonl
python -m src.cli eval-agent --dataset ./examples/eval/agent_eval.jsonl
```

---

## 第五部分：工程化与生产设计

### 5.1 配置管理

每个模块有 `config.yaml`（开发）和 `config.production.yaml`（生产）。

配置通过环境变量选择：
```powershell
$env:PERSONAL_AI_CONFIG="config.production.yaml"
```

API key 只从环境变量读取，不写进配置文件。

### 5.2 诊断命令 Doctor

| 命令 | 检查内容 |
|---|---|
| `doctor-config` | 配置文件、目录结构、依赖包、API key |
| `doctor-llm` | LLM client 能否初始化 |
| `doctor-llm --call-api` | 真实调用 LLM API 是否成功 |
| `doctor-mcp` | FastMCP 是否可用 |
| `doctor-rag` | RAG 后端是否可搜索、可问答 |
| `smoke-test` | 基本功能冒烟测试 |

### 5.3 Monorepo 与 Bounded Context

**为什么是四个独立项目而不是单体？**

| 职责边界 | 单体污染问题 |
|---|---|
| RAG（检索增强） | 工具调用的安全策略会混入检索逻辑 |
| Agent（工具执行） | 检索评估指标会混入 Agent 审计日志 |
| MCP（协议桥接） | 特定 RAG 实现细节会泄漏到协议层 |

**设计原则**：
- 每个子系统独立部署和测试
- 通过 CLI/API/MCP 组合使用
- 共享的是概念（工具注册、安全策略）而不是代码

**面试回答模板**：
> "这个项目采用 monorepo + bounded context 的架构。RAG、Agent、MCP 三个职责边界不同，如果写成单体，工具调用的安全策略、检索评估、API 服务会互相污染。每个子系统保持独立部署和测试，通过 CLI、API、MCP 协议组合。这体现了工程上的 bounded context 和 integration layer 思维。"

---

## 第六部分：面试高频 Q&A

### Q1：RAG 和微调（Fine-tuning）有什么区别？

RAG 不训练模型。它构建一个检索增强链路：文档 -> 切块 -> embedding -> 向量库 -> 检索 -> 重排 -> 证据 -> LLM 生成。核心是高质量检索和证据构造，不是模型参数更新。RAG 的优势是知识可更新（重新索引即可）、可追溯（有引用）、可控制（证据不足可拒答）。

### Q2：Hybrid Search 为什么比纯向量好？

向量搜索擅长语义相似，但对精确术语（人名、方法名、公式编号）不敏感。BM25 基于词频和 IDF，对精确匹配很强。两者融合后，既能理解"这篇论文的创新点是什么"这种语义查询，也能处理"Attention Is All You Need 这篇论文"这种精确查询。学术场景下很多查询包含专有名词，hybrid 更稳定。

### Q3：如何减少 RAG 的幻觉？

三层防线：
1. **检索层**：hybrid search 提高召回质量
2. **证据检查层**：`has_sufficient_evidence()` 在调用 LLM 之前检查证据是否充分
3. **生成层**：system prompt 强制 "只基于证据回答"，证据不足时返回固定拒答字符串
4. **评估层**：`refusal_accuracy` 指标持续监控拒答准确性

### Q4：Agent 和 Chatbot 的区别？

Chatbot 是自由文本生成。Agent 是在受控工具集合中规划、调用、记录和执行。关键区别：
- Agent 有 Tool Registry（工具注册表）
- Agent 有 risk_level 和 dry-run（安全分级）
- Agent 有 audit log（审计追踪）
- Agent 有 human-in-the-loop（人工确认）
- Agent 的输出是结构化的工具调用结果，不是自由文本

### Q5：为什么需要 MCP 这一层？

LLM 不能直接安全地访问文件系统或代码仓库。MCP 工具层提供：
- **工具发现**：`tools/list` 让模型自动知道有哪些能力
- **参数 Schema**：每个工具的输入输出有结构化定义
- **安全策略**：路径限制、敏感文件检测、dry-run
- **协议边界**：客户端与本地能力的标准接口
- **解耦**：通过 Adapter 模式不绑定具体 RAG 实现

### Q6：如何保证文件操作安全？

五层防线：
1. **PathGuard**：workspace 路径限制 + 路径穿越检测 + 符号链接逃逸检测
2. **SensitiveFileGuard**：`.env`、`*.key`、`*.pem` 等敏感文件模式匹配
3. **Dry-run**：写操作默认只生成计划
4. **Human confirmation**：高风险操作需要显式确认
5. **Audit log + Rollback**：所有操作记录，支持反向回滚

### Q7：为什么用 OpenAI Compatible 接口？
- **生态兼容**：支持 OpenAI、DeepSeek、通义千问、Anthropic 等多种后端
- **切换灵活**：改 `base_url` 和 `model_name` 即可切换不同供应商
- **标准化**：function calling、streaming、batch 等能力统一接口
- **本地也兼容**：Ollama、vLLM 暴露的同样是 OpenAI-compatible API

### Q8：这个项目的生产化做了什么？

- 配置管理（YAML + 环境变量，不硬编码）
- 诊断命令（doctor-config、doctor-llm --call-api）
- 安全机制（路径守卫、dry-run、确认、审计、回滚）
- API 认证（FastAPI token 保护）
- 可观测性（5 类 JSONL 日志）
- 评估体系（RAG eval + Agent eval）
- CI/CD（GitHub Actions）
- 容器化（Docker + docker-compose）
- 双语文档（中英文 README + 开发/使用文档）
- Release Checklist

### Q9：如果让你继续改进，你会做什么？

V2 已完成高级 RAG、GraphRAG、多 Agent、RAGAS/A-B 评估和 Next.js UI。下一步更有价值的方向是：
- 用户账户系统
- 本地模型支持（SentenceTransformers embedding、cross-encoder reranker、Ollama LLM）
- 人工标注的 held-out eval 集与持续质量监控
- 插件系统
- 更强的评估（人工评估、在线 A/B 与成本/延迟指标）
- 托管文档站点

### Q10：整个系统的数据流是什么？

```
本地材料 (PDF/Word/PPT/Markdown/TXT)
  -> DocumentLoader 策略模式解析
  -> TextChunker 滑动窗口切块 (chunk_size=800, overlap=120)
  -> SHA1 生成确定性 chunk_id
  -> BaseEmbeddingClient.embed_texts() 生成向量
  -> VectorStore.upsert() 写入 Chroma/JSON
  -> BM25Store 构建倒排索引

查询时：
  -> HybridRetriever.search()
    -> KeywordRetriever (BM25)
    -> SemanticRetriever (向量)
    -> 融合: 0.4*bm25 + 0.6*vector
  -> RuleReranker.rerank()
    -> 0.55*base + 0.30*coverage + 0.15*title_hit
  -> EvidenceChecker.has_sufficient_evidence()
  -> AnswerGenerator.answer()
    -> LLM.generate() with grounded prompt
    -> CitationBuilder.build_citations()
  -> Answer(text, citations, confidence, evidence)
```

### Q11：CRAG 是什么，为什么不用“分数低就直接拒答”？

CRAG 是把检索质量变成路由决策。直接拒答太保守，直接回答又可能幻觉；所以系统按 confidence 分为 high/medium/low：high 直接答，medium 扩大召回再试一次，low 才拒答。它像医生先看化验结果：明确就下结论，边缘就加做检查，完全没证据就不诊断。

### Q12：ReAct 和 Planner 有什么区别，什么时候选哪个？

Planner 先生成完整工具计划，适合“扫描 -> 生成报告”这种固定流水线；ReAct 每次调用后把 observation 回给模型，适合“先搜索，再根据结果决定读哪份文档”的探索任务。ReAct 多一次闭环就多一次成本和不确定性，因此代码用最大迭代、重复动作检测和 fallback planner 控制它。

### Q13：GraphRAG 和普通 RAG 的区别？

普通 RAG 找的是“和问题最像的段落”；GraphRAG 还把概念、概念共现关系和 chunk 链接建成图，先命中节点再扩展邻居。它像普通 RAG 只查图书馆目录，GraphRAG 还会查看“这本书引用了谁、和谁属于同一主题”的关系网。关系问题和跨文档问题更受益，但建图和维护成本更高。

### Q14：RAGAS 的四个指标分别看什么？

- `faithfulness`：答案有没有超出检索 context，像检查“学生是否只按资料答题”。
- `answer_relevancy`：答案是否真正回应问题，而不是相关但跑题。
- `context_precision`：召回的 context 前排是不是有用，像搜索结果第一页是否干净。
- `context_recall`：给定参考答案所需的信息是否已被召回，像资料是否找全。

它们不替代拒答准确率；`should_answer: false` 的样例由内置 refusal 指标单独评估。

---

## 第七部分：GraphRAG

**代码位置**：`personal-ai-workspace/src/graphrag/`

系统先用 SQLite 存 concept nodes、共现 edges、node-to-chunk links。查询时 `GraphRAGRetriever` 对 query token 找命中节点，扩展一跳邻居，再把关联 chunk 按节点命中权重排序：

```python
matching = {node["node_id"] for node in nodes if node["label"] in query_terms}
expanded = matching | {neighbor for node in matching for neighbor in adjacency[node]}
scores[link["chunk_id"]] += 1.0 if link["node_id"] in matching else 0.35
```

这是自建、可检查的图索引：能回答“attention 与哪个数据集/方法共同出现”。`LightRAGAdapter` 是可选生产适配器，它不重写模型客户端，而是把现有 `BaseLLMClient`、`BaseEmbeddingClient` 包装成 LightRAG 所需的异步回调；因此保留 OpenAI-compatible 配置、审计和替换能力。

**面试要点**：GraphRAG 不是替代 vector RAG。当前支持 `graphrag` 或 `hybrid+graphrag`，后者更适合兼顾语义召回和关系扩展。图里没有实体或关系很稀疏时，普通 hybrid 仍是可靠 fallback。

## 第八部分：多 Agent 协作

**代码位置**：`personal-ai-workspace/src/multi_agent/`

没有直接引入 CrewAI，而是自建三个很小的抽象：

```python
@dataclass(frozen=True)
class AgentRole:  # 身份、系统提示、可用工具、可选 LLM 覆盖
    ...
@dataclass(frozen=True)
class Task:       # 任务描述、负责角色、期望输出
    ...
class Crew:       # 按顺序把共享 state 传给每个 Task
    def run(self, input_data): ...
```

`run_research_crew()` 先统一检索 evidence，再顺序执行 Reader、Method、Experiment、Critic、Writer。每个角色读取相同 evidence 和之前的 `state["outputs"]`，Writer 最后整合而不是重新无依据地检索。

比喻：不是五个人各写一篇互相矛盾的报告，而是同一张资料桌上的五位专员。Reader 摘事实，Method 看方法，Experiment 看实验，Critic 找边界，Writer 合稿。失败被记录在 role/task 步骤里，角色还可以配置独立 LLM override。

## 第九部分：评估体系

评估分为三条互补路线：

1. **确定性 RAG eval**：`expected_sources`、关键词、引用、拒答、confidence，快且适合 CI。
2. **RAGAS**：用真实评审 LLM 计算 faithfulness、answer relevancy、context precision、context recall；只对有非空 `reference` 的可回答样例运行，非有限分数转成 JSON `null` 并记录原因。
3. **A/B 测试**：`compare_configs()` 深拷贝原配置，分别应用 A/B override，执行同一数据集，再输出 `delta_b_minus_a`。这避免“为了试一个权重把全局配置改坏”。

```python
left = _apply_overrides(config, config_a)
right = _apply_overrides(config, config_b)
return {"metrics_a": eval_rag(left, dataset)["metrics"],
        "metrics_b": eval_rag(right, dataset)["metrics"]}
```

面试时不要只报一个漂亮分数。应说明：离线确定性指标看回归，RAGAS 看生成质量，拒答样例单独看 refusal accuracy；最终还要有人工抽样审查引用是否真的支持结论。
