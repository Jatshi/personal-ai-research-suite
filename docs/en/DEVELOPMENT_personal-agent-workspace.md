# Development: personal-agent-workspace

## Core Idea

An Agent system is not just an LLM that writes text. It is an LLM or planner operating through controlled tools, state, safety policies, and logs:

```text
Agent -> Tool Registry -> Safety Layer -> Tool Execution -> Logs / State / Report
```

## Key Modules

- `src/tools/tool_registry.py`: tool registration, parameter validation, risk levels.
- `src/safety/`: path guard, dry-run, audit log, rollback.
- `src/agents/`: file organizer, thesis finishing, paper reading, work assistant.
- `src/workflows/`: state machine and multi-step workflows.
- `src/parsers/`: document and code parsers.
- `src/llm/`: mock and OpenAI-compatible LLM clients.
- `src/reporting/`: Markdown/JSON reports.

## ToolSpec Design

Each tool declares:

```python
name: str
description: str
input_schema: dict
risk_level: low | medium | high
requires_confirmation: bool
```

This prevents the Agent from directly manipulating the filesystem without centralized safety checks.

## Safety Design

- Workspace path restriction.
- Dry-run for write operations.
- Human approval before execution.
- JSONL audit logs for every tool call.
- Rollback records for move/rename.
- Secret and hidden-file blocking by default.

## Multi-Agent Paper Reading

The workflow has five roles:

1. Reader Agent: read paper and extract metadata.
2. Method Agent: summarize method and innovations.
3. Experiment Agent: extract datasets, metrics, baselines, results.
4. Critic Agent: analyze limitations and reproducibility.
5. Writer Agent: produce Markdown note and comparison table.

## Interview Talking Points

- Difference between an Agent and a chatbot.
- Why tool calling needs schemas and risk levels.
- Why risky file operations require dry-run.
- How human-in-the-loop approval is implemented.
- How JSONL logs provide traceability.
- Why mock LLMs are useful for offline testing.
