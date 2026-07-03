# Agent Harness Notes

An Agent Harness is an engineering layer around an LLM. It manages tool schemas, tool calls, state, safety checks, dry-run execution, human approval, and audit logs.

The important design is that high-risk tools such as write_note and write_todo require dry-run and confirmation. This prevents an agent from silently modifying local files.

