# ReAct: Synergizing Reasoning and Acting in Language Models

Source: https://arxiv.org/abs/2210.03629

ReAct interleaves reasoning traces with actions such as search or environment
steps. Each action returns an observation that can change the next reasoning
step. The paper evaluates knowledge-intensive reasoning and interactive tasks,
including HotpotQA and ALFWorld. ReAct differs from a fixed plan because it can
adapt after seeing tool observations, while still requiring bounded loops and
safe tool execution in production systems.
