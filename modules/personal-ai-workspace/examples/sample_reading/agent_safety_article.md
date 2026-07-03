# AI Agent Safety

Agent safety depends on tool boundaries. A safe local agent should not directly edit files without dry-run, confirmation, workspace restriction, and audit logging.

Prompt injection can ask an agent to ignore previous instructions or exfiltrate secrets. The system should block sensitive file access and keep structured logs.

