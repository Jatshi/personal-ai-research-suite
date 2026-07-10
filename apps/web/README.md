# ScholarMind Web

The Phase 6G Next.js workbench is a parallel UI for the existing Streamlit app.

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

It consumes FastAPI REST and SSE endpoints.

Current API-backed routes:

- Dashboard: `/dashboard/summary`
- Import: `/kb/ingest`
- Search: `/rag/ask/stream`
- Agent: `/agent/chat/stream`
- Paper Reading: `/agents/crew/run` and
  `/integrations/agent-workspace/read-papers`
- Observability: `/observability/logs`
- System health: `/observability/health`
- Settings: `/settings/public` and `/llm/doctor`

Search exposes request-scoped retrieval controls for mode, query rewrite, context
compression, CRAG routing, and multi-hop retrieval. Settings changes are previewed
first and require a separate confirmation request before the local YAML changes.
The Agent sidebar reads its current session's filtered durable-memory summary;
long-term memory is empty unless explicitly enabled on the backend.
Dashboard query metrics and the seven-day activity chart are calculated from the
local RAG JSONL log, not a hosted analytics service.

Browser file uploads use `/kb/upload`; the backend accepts PDF, DOCX, PPTX,
Markdown, TXT, and HTML, stores each file in the workspace raw-data area, then
uses the normal indexing pipeline. Collection, comma-separated tags, chunk size,
and overlap are request-scoped import metadata; they do not rewrite global YAML.

The File Organizer, Thesis Check, and batch Paper Reading views expose constrained
sibling-module bridge calls using paths below `personal-agent-workspace/workspace/`.
The organizer is always a dry-run preview, the thesis route is report-only, and
batch paper reading writes derived notes only below the sibling module's export
directory. Keep the API token in browser-safe development environment configuration
only when the FastAPI server enables token auth.
