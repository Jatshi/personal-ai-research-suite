# 学习疑问与解答归档

> 本文档归档在阅读 ScholarMind AgentOS 技术文档过程中产生的疑问及详细解答。
> 所有解答以"说人话"为原则，力求通俗易懂。

---

## 一、RAG 部分

### 1. 递归字符切分是什么？我的系统按段落边界切是什么意思？

**递归字符切分**（Recursive Character Text Splitter）是 LangChain 的一种切块策略。

打个比方：你想把一根很长的香肠切成 800g 一段。你先试着在"粗节"处（双换行 `\n\n` = 段落边界）切，如果切出来还是太长，就在"细节"处（单换行 `\n` = 行边界）切，再不行就在空格处切，最后实在不行就硬按字符数切。

它有一个分隔符优先级列表：`["\n\n", "\n", " ", ""]`，逐级降级。

**你的系统**的做法更直接：把段落一个一个往 buffer 里塞，塞到快超过 `chunk_size`（800字）就切一刀。只在段落边界切，不会把一个段落从中间劈开。只有当某个段落自己就超过 `800 * 1.5 = 1200` 字时，才会强制硬切。

**一句话区别**：
- 递归切分 = 有多级退路，实在不行就硬切字符
- 你的系统 = 只在段落边界切，段落太长才例外硬切

---

### 2. 文本哈希是什么？有什么用？幂等 upsert 是啥玩意？

**文本哈希**：把任意长度的文本通过哈希函数（如 SHA1）变成一个固定长度的字符串。比如 `SHA1("RAG 是什么")` 可能得到 `a3f2b1c8...`。关键特性：同样的文本永远得到同样的结果，哪怕改一个字结果就完全不同。

**用途**：你的系统用文本哈希生成 chunk_id。`make_chunk_id(doc_id, index, text[:200])` = SHA1(doc_id + 序号 + 文本前200字)[:12]。这样每个 chunk 有一个全局唯一、确定性、可回溯的 ID。

**幂等 upsert** 拆开看：
- 幂等 = 同一个操作执行一次和执行一百次，结果完全一样
- upsert = update + insert，ID 存在就更新，不存在就插入

合起来就是：你把同一份文档导入两次，因为 chunk_id 是根据内容算出来的，两次算出的 ID 一样，第二次就会覆盖而不是重复添加。不会产生重复数据。网络中断后重试也安全。

---

### 3. chunk 和 embedding 之间的关系是什么？切块完之后如何变成嵌入向量？n-gram 是什么？

**关系**：chunk 是"切好的文本块"，embedding 是"这个文本块对应的数字向量"。一个 chunk 对应一个 embedding 向量。

流程是：
```
原文档 → 切块 → 每块 chunk.text → embedding_client.embed_texts() → 浮点向量 → 存入向量库
```

**切块后如何变成向量**：

1. 把 chunk 文本列表发给 Embedding API（如 OpenAI、兼容接口、SentenceTransformers）
2. API 返回每段文本的向量（浮点数列表，如 384 维或 1536 维）

**n-gram**：把连续的 n 个字当做一个词。比如"注意力机制"这个词：
- 2-gram：注意、意力、力机、机制
- 3-gram：注意力、意力机、力机制

你的系统对中文用 2-gram 和 3-gram，不需要词典就能分词，且能捕获部分语义。

---

### 4. 检索层和索引层有啥区别？检索的 keyword 和 semantic 不就对应的是向量检索和 BM25 检索吗？

**索引层 = 写入阶段**：把数据存进去。`BM25Store` 在初始化时遍历所有 chunk，构建词频表和倒排索引。`VectorStore` 在 `upsert()` 时把向量写入 Chroma/JSON。这就像把书放进图书馆并建好索引卡片。

**检索层 = 读取阶段**：从索引中查找。`KeywordRetriever` 和 `SemanticRetriever` 封装了查询逻辑，加上 filter、top_k 参数。这就像去图书馆用索引卡片找书。

**为什么要分两层**：索引层只管"把数据存好"，检索层管"怎么查、查多少、怎么过滤、怎么融合"。职责分离后，检索层可以做 HybridRetriever 把两个索引器的结果融合，而索引层不需要关心这些。

你的理解是对的：keyword 对应 BM25，semantic 对应向量。检索层就是在这两个索引层之上包了一层查询接口。

---

### 5. reranker 是什么？为什么要重排？cross-encoder reranker 是什么？

**reranker = 重排器**：在检索器召回结果之后，对结果重新排序的组件。

**为什么要重排**：检索器的分数不够精准。BM25 只看词频（"这个词出现了几次"），向量搜索只看语义相似（"向量距离近不近"）。但有时候排第一的结果其实和问题没啥关系，只是碰巧关键词多或语义接近。reranker 用额外信号来修正排序。

你的系统用规则重排，三个信号：
- 基础检索分（55%）：检索器给的分数
- 关键词覆盖率（30%）：问题中的词有多少出现在了这个 chunk 里
- 标题命中（15%）：问题的词有没有出现在文件名/标题中

**cross-encoder reranker**：一种基于预训练模型的重排器。它把"问题"和"候选 chunk"拼成一句话，送进 BERT，直接输出一个相关性分数。比分别编码再算相似度（bi-encoder）更准确，但慢得多。你的系统当前用的是规则重排（不依赖外部模型），cross-encoder 是可选的升级方向。

---

### 6. 置信度计算的几个指标具体指的是什么？为什么要算？

confidence_score 公式：`0.45 * top + 0.25 * count_factor + 0.30 * coverage`

| 维度 | 权重 | 含义 | 人话 |
|---|---|---|---|
| `top` | 45% | 检索结果中最高分 | 最好的证据质量有多高 |
| `count_factor` | 25% | 结果数量 / 5，上限 1.0 | 知识库对这个问题覆盖得多不多 |
| `coverage` | 30% | 问题中的词在 chunk 中出现的比例 | 证据和问题有多相关 |

另外，如果 coverage = 0（问题中的词一个都没出现在证据里），直接给低分 `min(0.2, 0.45 * top)`，封顶 0.2。

**为什么要算**：
- 决定是否拒答：confidence < 0.35 就不调 LLM，直接说"证据不足"，防止幻觉
- 给用户参考：这个答案有多可信
- 评估用：eval 时统计平均置信度，判断系统整体质量

---

### 7. RAG 输出的结果是什么？搜寻到的有效信息以什么样的方式给到上下文？

**输出**是 `Answer` 对象：
- `text`：LLM 生成的回答 + 拼接的引用列表
- `citations`：引用列表（序号 + 文件名 + 页码 + chunk_id）
- `confidence`：置信度分数
- `evidence`：检索到的证据片段列表

**证据如何给到 LLM**：

在 `AnswerGenerator` 中，每个检索结果被转成字典：
```python
context = [{"text": chunk.text, "chunk_id": ..., "filename": ..., "page": ..., ...}]
```

然后在 `OpenAICompatibleLLMClient.generate()` 中，这些 context 被格式化成：
```
[1] paper.pdf page=3 paragraph=2 chunk_id=abc123
这是第一段证据的原文内容...

[2] notes.md page=None paragraph=1 chunk_id=def456
这是第二段证据的原文内容...
```

放在 user message 的 `Evidence:` 部分。同时 system message 告诉 LLM："你是学术 RAG 助手，只基于证据回答，证据不足就回答固定拒答字符串，引用时用方括号编号。"

**简单说**：检索到的每个 chunk 文本，带上来源信息（文件名、页码、chunk_id），格式化成带编号的文本块，拼在一起塞进 LLM 的上下文里。LLM 被要求"只能基于这些证据回答"。

---

### 8. CRAG 自适应路由是什么？

**CRAG 可以理解为“检索结果的分诊台”。** 普通 RAG 拿到结果后往往直接回答；CRAG 会先问：这批材料到底靠不靠谱？

像你去医院：
- 化验很明确，医生直接给结论（`high`）。
- 有点线索但不够，医生让你多做一项检查（`medium`，扩大 top-k 再检索）。
- 完全没有证据，医生不会给你编一个病名（`low`，固定拒答）。

代码并不神秘，就是把 confidence 映射成三条路：

```python
confidence = confidence_score(query, chunks)
if not chunks or confidence < min_confidence:
    return RouteDecision("low", confidence, "insufficient_evidence")
if confidence < min(0.75, min_confidence + 0.25):
    return RouteDecision("medium", confidence, "expand_retrieval")
return RouteDecision("high", confidence, "direct_answer")
```

重点：`low` 不是“系统坏了”，而是系统诚实地说“我没有足够材料”。这正是降低幻觉的关键。

### 9. 上下文压缩为什么要做？

检索到的 chunk 越多，不代表模型越聪明。把十几段全文都塞进去，像让一个人从一大摞打印纸里找一句话：成本上升，重点反而被淹没，还可能超过上下文窗口。

你的系统有两种压缩：
- **token budget**：按分数优先装入高价值片段，像行李箱先装必需品。
- **extractive**：只抽原 evidence 里和问题相关的句子，不凭空写摘要，像从原书贴便签。

```python
item["text"] = first_sentences(text, remaining)
item["compressed_from_chunk_id"] = chunk.get("chunk_id")
```

最后一行很重要：压缩后仍保存原来的 `chunk_id`。所以引用没有断，用户还能回到真正的原文核对。

### 10. GraphRAG 和普通 RAG 区别？

普通 RAG 是“按相似度找段落”：问题像哪段文字，就把哪段拿回来。

GraphRAG 多了一张“关系网”：概念是节点，概念在同一 chunk 里出现就连边，节点再连接回原 chunk。它更适合问“方法 A 和数据集 B 有什么关联”“某个概念跨哪些论文出现”。

```python
matching = {node["node_id"] for node in nodes if node["label"] in query_terms}
expanded = matching | {neighbor for node in matching for neighbor in adjacency[node]}
```

比喻：普通 RAG 是查书名目录；GraphRAG 还会翻这本书的引用关系和主题关系网。代价是需要建图、更新图；当图很稀疏或问题只是找一段定义时，普通 hybrid RAG 往往更直接。

### 11. RAGAS 四个指标分别衡量什么？

RAGAS 是让另一个 LLM 以“阅卷老师”视角审查 RAG 输出。四个常用指标不是同一件事：

| 指标 | 说人话 | 类比 |
|---|---|---|
| Faithfulness | 答案是否只来自给它的 context | 是否只按教材答题，没有瞎加课外结论 |
| Answer Relevancy | 答案是否真正回答了问题 | 没有答非所问 |
| Context Precision | 排在前面的检索材料是否有用 | 搜索结果第一页是否干净 |
| Context Recall | 参考答案需要的信息是否被找全 | 复习资料是否漏了关键知识点 |

```python
metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()]
result = evaluate(dataset=EvaluationDataset(samples=samples), metrics=metrics)
```

注意：RAGAS 不适合衡量“该不该拒答”。你项目把 `should_answer: false` 留给确定性的 `refusal_accuracy`，避免拿错误的尺子量错误的问题。

## 二、Agent 系统

### 1. JSON Schema 风格是什么

打个比方：你在填一个报名表，每个输入框旁边都有说明——"这里填你的名字（文字）""这里填年龄（数字）""这个框必须填"。

JSON Schema 就是把这种"表单说明"写成机器能读懂的 JSON 格式。你的系统中每个工具的 `input_schema` 就是这么写的：

```json
{
    "type": "object",           // 参数整体是一个对象（字典）
    "properties": {             // 有哪些字段
        "path": {"type": "string"},      // path 字段是字符串
        "max_chars": {"type": "integer"} // max_chars 字段是整数
    },
    "required": ["path"]        // path 是必填的
}
```

**好处**：
- LLM 看到 schema 就知道"这个工具要什么参数、什么类型、哪些必填"，能自动生成正确的调用
- 程序代码也能用这个 schema 自动校验参数（`_validate_params` 就在做这事）
- 和 OpenAI function calling、MCP 协议都兼容，是行业通用格式

### 2. Tool Registry 设计包含什么？一个工具如何被设计出来？对话中如何识别并调用？

**Tool Registry = 工具登记簿/工具箱**。你的系统里，每个工具 = ToolSpec（说明书）+ 执行函数（实际干活的人）。

**ToolSpec 包含什么**：
- `name`：工具名（如 `scan_folder`）
- `description`：描述（给 LLM 看的，让它知道这工具干嘛的）
- `input_schema`：参数说明（要什么参数、什么类型、哪些必填）
- `risk_level`：`low` / `medium` / `high`
- `requires_confirmation`：要不要人工确认

**代码层面怎么注册一个工具**：
```python
registry.register(
    ToolSpec(
        name="scan_folder",
        description="Scan workspace folder",
        input_schema={"required": ["path"]},
        risk_level="low",
        requires_confirmation=False
    ),
    lambda path: scan_folder(path)  # 实际执行的函数
)
```

**对话中如何识别并调用**：两种方式同时存在——

| 方式 | 原理 | 特点 |
|---|---|---|
| **规则 Planner** | 关键词匹配 | 看 goal 里有没有"整理"/"organize"/"文件"，匹配到就推荐 scan_folder | 确定性强、零延迟、不花钱 |
| **LLM Planner** | 语义理解 | 把 ToolSpec 列表发给 LLM，LLM 自己判断哪个工具最合适 | 更灵活（比如"把桌面垃圾收拾一下"LLM 也能理解是 organize），但需要 API、可能出错 |

不是单纯的"关键词识别"也不是单纯的"语义识别"，而是**双保险**：默认规则 planner，有 API 时用 LLM planner，LLM 出错就回退到规则 planner。

---

### 3. Pydantic 是什么？为什么可以不手写 JSON Schema？

**Pydantic** 是 Python 的数据验证库。你可以用 Python 类定义数据结构，Pydantic 自动帮你：
- 做类型检查（"这里应该传字符串，你传了数字就报错"）
- 做参数校验（"这个字段必填，你漏了就报错"）
- **自动生成 JSON Schema**

**示例**：
```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str           # 必填字符串
    top_k: int = 5       # 整数，默认 5

# 自动生成的 JSON Schema：
# {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]}
```

**为什么你的项目手写 JSON Schema 而不是用 Pydantic**：
1. **学习底层**：手写 `_validate_params` 让你理解校验到底在做什么
2. **灵活性**：手写可以做 Pydantic 不支持的特殊校验（比如中文关键词映射）

**但你的项目其实也在用 Pydantic**：FastAPI 的接口参数就是用 Pydantic 定义的（`SearchRequest`、`AskRequest` 等）。所以是"工具层手写，API 层用 Pydantic"，各取所长。

---

### 4. 为什么整个项目倾向于从零自建，不用 LangChain？

你说得完全对。**这个项目的核心目的就是学习底层实现，而不是调包**。

LangChain 的问题：
- 封装太厚，你用了它的 Tool、Agent、Chain，但不知道里面在做什么
- 很多设计决策被藏起来了（比如切分策略、安全策略、评估逻辑）
- 面试时如果只会调包，面试官一问深就答不上来

自建的好处：
- **理解每个设计决策**：为什么 chunk_size=800？为什么 BM25 的 k1=1.5？你都知道
- **按需定制**：LangChain 没有 risk_level、dry-run、confirmation 这些概念，你需要自己实现
- **面试能力展示**：面试官想看的是你会不会设计系统，而不是会不会调包

一句话：**LangChain 是别人的工具箱，自建是你自己的工具箱。用别人的，面试时说不清；建自己的，每个螺丝你都拧过。**

---

### 5. 怎么判断一个文件名是否敏感？

`SensitiveFileGuard` 用 `fnmatch`（Unix shell 风格）做模式匹配：

```python
SENSITIVE_PATTERNS = [
    ".env",      # 精确匹配 .env
    "*.env",     # 匹配任何 .env 结尾的文件（如 config.env）
    "*.key",     # 匹配任何 .key 结尾的文件
    "*.pem",     # SSL 证书私钥
    "*.crt",     # 证书文件
    "id_rsa",    # SSH 私钥
    "id_ed25519",# SSH 私钥
    "credentials.json",  # Google 认证文件
    "secrets.*", # 任何 secrets. 开头的文件
    "*.token",   # token 文件
]
```

检查逻辑：把文件名和每个 pattern 做 `fnmatch.fnmatch(name, pattern)` 匹配。匹配上了就是敏感文件，拒绝访问。

**为什么是 fnmatch 而不是精确匹配**：因为敏感文件有各种变体（`config.env`、`local.env`、`api.key`），用模式匹配可以覆盖一类文件。

---

### 6. dry-run 是什么意思？

**Dry-run = 演习 / 模拟运行**。就像军演不开真枪，只走流程。

在文件操作中，dry-run = **只生成操作计划，不真正执行**。比如：
- 你要整理文件，dry-run 模式下系统告诉你："我要把 `file1.txt` 重命名为 `2025_notes_v1.txt`，把 `draft_v2.md` 移到 `notes/` 文件夹"
- 但实际上**不动任何文件**

你确认计划没问题后，再带上 `--execute --yes` 真正执行。

**为什么要 dry-run**：
- 防止误操作：先看看计划对不对，错了可以改
- 可审计：计划本身就是一份"操作意图"记录
- Agent 安全：高风险工具默认 dry-run，不让 AI 随便改你文件

---

### 7. Audit Log 和 Rollback 是什么，做了什么事情？

**Audit Log = 审计日志 = "操作记录仪"**。记录每次工具调用的完整信息：
- 做了什么操作（工具名）
- 用了什么参数
- 结果成功还是失败
- 是否 dry-run
- 时间戳

格式是 JSONL（每行一条 JSON），适合流式写入和后续分析。

**Rollback = 回滚 = "撤销功能"**。每次移动/重命名文件时，额外记录**反向操作**：
- 把 `A.txt` 移到 `notes/B.txt` → 记录撤销信息："把 `notes/B.txt` 移回 `A.txt`"
- 把 `old_name.md` 重命名为 `new_name.md` → 记录撤销信息："把 `new_name.md` 改回 `old_name.md`"

之后如果发现操作有误，可以执行 `execute_latest_rollback()`，自动按最近记录还原。

**一句话**：Audit log 是"记账本"（记你做了什么），Rollback 是"后悔药"（让你能撤销）。

---

### 8. 规则 planner 和 LLM planner 的区别是什么？

| 维度 | 规则 Planner | LLM Planner |
|---|---|---|
| **原理** | 关键词匹配 | 把 ToolSpec 发给 LLM，让它自己选 |
| **示例** | 用户说"整理文件" → 匹配"整理"关键词 → 调用 organize_files | 用户说"把桌面垃圾收拾一下" → LLM 理解这是 organize → 生成 JSON 计划 |
| **优点** | 零延迟、零成本、确定性强 | 灵活、能理解复杂/模糊的表达 |
| **缺点** | 死板，只能匹配预定义关键词 | 需要 API key、可能出错（编造不存在的工具）、有成本 |
| **何时用** | 默认、LLM 出错时回退 | 有真实 LLM、用户表达复杂时 |

**你的系统两者都用**：默认规则 planner，配置中启用 LLM 时用 LLM planner，LLM 返回非法内容时自动回退到规则 planner。

---

### 9. 文件整理、论文阅读、博士论文检查，这些都是工具吗？

**是的，但不完全是"同一个层级的东西"**。

更准确地说，分为两层：

**底层工具（Tool）**：原子操作，不可再分
- `scan_folder`：扫描文件夹
- `move_file`：移动文件
- `rename_file`：重命名文件
- `read_paper`：读取论文

**上层工作流/Agent**：把多个工具按顺序组合
- **文件整理** = scan_folder（扫描）→ find_duplicates（查重）→ suggest_file_rename（建议新名）→ move_file/rename_file（执行）
- **论文阅读** = read_paper（Reader）→ extract_method（Method）→ extract_experiment（Experiment）→ analyze_limitations（Critic）→ generate_note（Writer）
- **博士论文检查** = check_thesis_structure（章节结构）→ check_figure_table_references（图表编号）→ check_bibliography_references（参考文献）→ generate_todo_list（生成待办）

在代码里，这些工作流也是通过 `registry.register()` 注册为工具的（比如 `read_papers` 就是一个组合工具）。用户可以单独调用某个原子工具，也可以让 Agent 按工作流自动调用多个工具。

---

### 10. ReAct 循环怎么工作的？

**ReAct = Reason + Act，可以理解成“边走边看导航的 Agent”。**

Planner 像出门前一次性写好路线：先坐地铁，再走路，再到目的地。ReAct 则是走到一个路口后看一眼导航（工具结果），再决定下一步。它特别适合“先搜索资料，看看搜到什么，再决定读哪篇”的任务。

当前代码不要求暴露模型的私有 Thought，而是保留安全、可审计的闭环：

```python
response = llm.complete_with_tools(state.messages, registry.openai_tools())
call = response.tool_calls[0]             # Action：模型选择一个工具
result = registry.call(call.name, call.arguments)  # 执行仍经过安全 Registry
state.messages.append({                   # Observation：结果回给模型
    "role": "tool", "tool_call_id": call.call_id,
    "content": json.dumps(result),
})
```

然后模型继续下一轮，直到它不再请求工具。为了不让 Agent 原地绕圈，系统还有：最大迭代次数、相同调用去重、参数修复上限；原生 tool calling 的 provider 报错时，会降级到经过校验的 JSON planner。

比喻：ReAct 不是让 AI 拿到万能钥匙，而是让它每次只能提出“我想按这个按钮”，系统按完后把仪表盘读数给它看。真正的按键权限仍在 `ToolRegistry` 手里。

## 三、MCP 工具协议层

### 1. MCP 有啥用？这个项目为什么要用 MCP？

**MCP = Model Context Protocol = "AI 模型的万能遥控器"**。

打个比方：你家有电视、空调、机顶盒，每个都有不同的遥控器。MCP 就是**万能遥控器**——统一格式，一个遥控器控制所有设备。

这个项目用 MCP 是为了：**让外部 AI（如 Claude Desktop、Cursor、IDE Agent）能安全地调用你本地的 RAG、文件系统、代码仓库能力**。

具体场景：
- 你在 Claude Desktop 里问："帮我搜索一下我本地论文库里关于 RAG 的内容"
- Claude 不知道怎么访问你的本地文件
- MCP 就是中间的桥梁——Claude 通过 MCP 协议发现你本地有哪些工具，然后调用 `search_documents` 工具完成搜索
- 整个过程 Claude 不需要知道你的文件在哪里、用什么格式存储

**为什么要用 MCP 而不是直接写 API**：
- MCP 是**协议标准**，任何支持 MCP 的 AI 客户端都能连接，不需要为每个客户端单独开发
- MCP 内置**工具发现**：AI 自动知道"你有什么能力"，不需要硬编码
- MCP 内置**安全策略**：risk_level、dry-run、confirmation 都在协议层

---

### 2. MCP 到底是个啥？JSON-RPC over stdio / SSE 是什么？

你理解得基本对。**MCP 确实就是"让 AI 能调用本地服务的方法"**，但它和普通 API 有几个关键区别：

| 普通 API | MCP |
|---|---|
| 开发者主动调用 | AI 客户端**主动发现**"有什么工具可用" |
| 需要看文档才知道有哪些接口 | `tools/list` **自动列出**所有可用工具 |
| 参数靠人写 | 参数有 JSON Schema，**AI 自动生成** |
| 安全由外部网关负责 | **内置** risk_level、dry-run、confirmation |
| 一个服务一个接口 | **统一协议**，所有能力通过一个入口暴露 |

**JSON-RPC over stdio**：
- JSON-RPC = 一种通信格式（你问我答，每条消息都是 JSON）
- stdio = 标准输入输出 = **命令行黑窗口**
- 合起来就是：MCP Server 和 AI 客户端通过在命令行里"你一行 JSON 我一行 JSON"来通信

**SSE（Server-Sent Events）**：
- 另一种通信方式，通过 HTTP 长连接推送消息
- 适合 Web 场景，比如浏览器里的 AI 应用

**你说的"能被 AI 模型读懂的 API 文档"这个比喻很准确**。但 MCP 比普通 API 文档更进了一步——不是"你来看文档"，而是"AI 自动读取文档并生成调用"。

---

### 3. RAG Bridge 与 Adapter 模式我完全看不懂

我换个你一定能懂的比喻。

**场景**：你家有各种智能灯泡——Philips、Yeelight、小米。每个品牌的控制方式都不一样。

**Adapter 模式**：你买一个**万能网关**（Adapter），它对外提供统一的接口（开灯/关灯/调亮度），内部把命令翻译成每个灯泡能听懂的语言。

**RAG Bridge**：MCP toolkit 需要调用 RAG 能力，但它不想绑定某个具体的 RAG 系统（比如 `personal-ai-workspace` 或 `personal-academic-rag-workspace`）。所以它在中间加了一个**翻译官**（`LocalCliRagAdapter`）：

```
AI 说："帮我搜索 RAG 相关内容"
    ↓
MCP toolkit 说："search_documents('RAG')"
    ↓
Adapter（翻译官）说：
    "去 personal-ai-workspace 目录下运行：
     python -m src.cli search --query 'RAG'"
    ↓
personal-ai-workspace 执行搜索，返回 JSON 结果
    ↓
Adapter 把结果翻译回 MCP 格式
    ↓
MCP toolkit 返回给 AI
```

**代码层面**（`local-mcp-toolkit/src/rag/adapters.py`）：
```python
class LocalCliRagAdapter:
    def search_documents(self, query, top_k=5):
        cmd = [sys.executable, "-m", "src.cli", "search", "--query", query, "--top-k", str(top_k)]
        proc = subprocess.run(cmd, cwd=self.project_path, capture_output=True, timeout=90)
        return json.loads(proc.stdout)
```

**为什么要这么绕**：
1. **解耦**：MCP toolkit 和 RAG 项目是**独立进程**，不需要 import 对方的代码
2. **可替换**：今天用 personal-ai-workspace，明天可以换成别的 RAG 系统，只要 CLI 接口一样就行
3. **安全隔离**：RAG 系统在自己的进程里运行，崩溃了不会影响 MCP toolkit
4. **配置注入**：通过环境变量 `PERSONAL_AI_CONFIG` 指定生产配置，不修改目标项目文件

**一句话**：Adapter 就是**翻译官**。你（MCP）说中文，RAG 系统说英文，Adapter 在中间翻译，让你们能沟通但互不依赖。

### 4. 索引层写入了什么格式的数据？倒排索引是什么？直观解释

**向量索引**写入了：每个 chunk 对应一个浮点数列表（向量），比如 `[0.12, -0.34, 0.01, ..., 0.56]`（384 个数字）。存到 Chroma 数据库或 JSON 文件中。查的时候算"问题向量"和"所有 chunk 向量"的距离，距离近的排前面。

**BM25 索引（倒排索引）**写入了什么？用一个具体例子说明。

假设你有 3 个 chunk：

```
chunk_001: "RAG 使用向量检索增强生成"
chunk_002: "RAG 使用 BM25 做关键词检索"
chunk_003: "向量数据库存储嵌入向量"
```

`tokenize()` 之后，代码里实际存了两个数据结构：

**① df 表（document frequency）**——每个 token 出现在多少个 chunk 中：

```
"rag"      -> 2  (chunk_001, chunk_002)
"使用"     -> 2  (chunk_001, chunk_002)
"向量"     -> 2  (chunk_001, chunk_003)
"检索"     -> 2  (chunk_001, chunk_002)
"增强"     -> 1  (只有 chunk_001)
"生成"     -> 1  (只有 chunk_001)
"bm25"     -> 1  (只有 chunk_002)
"关键词"   -> 1  (只有 chunk_002)
"数据库"   -> 1  (只有 chunk_003)
"存储"     -> 1  (只有 chunk_003)
"嵌入"     -> 1  (只有 chunk_003)
```

**② doc_tokens**——每个 chunk 的 token 列表（用来算 tf = 词频）：

```
chunk_001 tokens: ["rag", "使用", "向量", "检索", "增强", "生成"]
chunk_002 tokens: ["rag", "使用", "bm25", "关键词", "检索"]
chunk_003 tokens: ["向量", "数据库", "存储", "嵌入", "向量"]
```

**这就是倒排索引的核心**：不是"文档里有什么词"（正排），而是"这个词出现在哪些文档里、出现几次"（倒排）。

**搜索时怎么用**：你搜"RAG 检索"，tokenize 得到 `["rag", "检索"]`。遍历每个 chunk：
- chunk_001："rag" 出现 1 次 + "检索" 出现 1 次 → 算 BM25 分数
- chunk_002：同上 → 算 BM25 分数
- chunk_003：两个词都没出现 → 分数 0，跳过

**IDF 的作用**：如果"使用"在所有 chunk 里都出现（太常见），IDF 就低，对排序贡献小。而"增强"只在 1 个 chunk 出现，IDF 很高，一旦匹配就加分。这就是 IDF 的"稀有词加分"逻辑。

**一句话**：倒排索引 = 一张"词 → 出现在哪些文档"的映射表。搜索时查表快速定位相关文档。

---

### 5. 为什么 LLM 能看懂 MCP？

**LLM 并不是直接"看懂 MCP 协议"**。真实过程分四步：

**第一步：AI 客户端（如 Claude Desktop）替 LLM 做协议解析。**

MCP Server 启动时，AI 客户端通过 `tools/list` 拿到工具列表，拿到的是 JSON：

```json
{
  "name": "search_documents",
  "description": "Search your local document collection",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query"},
      "top_k": {"type": "integer", "description": "Max results"}
    },
    "required": ["query"]
  }
}
```

**第二步：AI 客户端把这些工具信息拼进 LLM 的 prompt，变成自然语言。**

```
You have access to the following tools:
- search_documents: Search your local document collection
  Parameters: query (string, required), top_k (integer)
- read_file: Read a file from workspace
  Parameters: path (string, required)
```

**第三步：LLM 看到的是自然语言描述 + JSON Schema，不是 MCP 协议本身。**

LLM 训练时就学过大量 JSON Schema 和 function calling 的格式（OpenAI function calling 用的就是同样格式）。所以它能理解"这个工具要什么参数"，然后生成调用。

**第四步：AI 客户端把 LLM 的输出转回 MCP 协议调用。**

LLM 输出 `{"tool": "search_documents", "params": {"query": "RAG"}}`，AI 客户端把它包装成 MCP 的 `tools/call` 请求发给 MCP Server。

**整个链路**：

```
MCP Server (JSON-RPC) ←→ AI 客户端 (协议翻译) ←→ LLM (看的是自然语言 + JSON Schema)
```

**一句话**：LLM 从来不直接处理 MCP 协议。它看到的就是一段文字说"你可以用这些工具，参数长这样"，然后输出"我要用这个工具，参数是这个"。AI 客户端在中间做翻译。
