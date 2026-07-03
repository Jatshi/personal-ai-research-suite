# 开发文档：personal-agent-workspace

## 核心思想

Agent 系统不是让 LLM 随便输出文字，而是让 LLM 在受控工具集合中规划、调用、记录和执行。这个项目的核心是：

```text
Agent -> Tool Registry -> Safety Layer -> Tool Execution -> Logs / State / Report
```

## 关键模块

- `src/tools/tool_registry.py`：统一注册工具、校验参数、控制风险级别。
- `src/safety/`：路径限制、dry-run、审计日志、rollback。
- `src/agents/`：文件整理、论文收尾、论文阅读、工作助理 Agent。
- `src/workflows/`：状态机和多步骤流程。
- `src/parsers/`：文档和代码解析。
- `src/llm/`：mock 与 OpenAI-compatible LLM。
- `src/reporting/`：Markdown/JSON 报告。

## ToolSpec 设计

每个工具声明：

```python
name: str
description: str
input_schema: dict
risk_level: low | medium | high
requires_confirmation: bool
```

这样 Agent 规划时不会直接操作文件系统，而是通过统一工具层。

## 安全机制

- workspace path restriction：工具只能访问允许范围。
- dry-run：写操作先生成计划。
- human approval：执行前确认。
- audit log：记录每次工具调用。
- rollback：move/rename 保存反向操作。
- secret blocking：默认不读 `.env` 和隐藏敏感文件。

## 多 Agent 论文阅读

流程由多个角色组成：

1. Reader Agent：读取论文、抽取元信息。
2. Method Agent：总结方法。
3. Experiment Agent：整理数据集、指标、结果。
4. Critic Agent：分析局限性和可复现性。
5. Writer Agent：整合成 Markdown note 和比较表。

## 面试可讲点

- Agent 与 Chatbot 的区别。
- Tool Calling 为什么需要 schema 和风险分级。
- 为什么高风险文件操作必须 dry-run。
- 如何设计 human-in-the-loop。
- 如何用 JSONL 做可追踪审计。
- 如何让 mock LLM 保证离线测试。
