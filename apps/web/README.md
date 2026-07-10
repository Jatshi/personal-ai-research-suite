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
- Paper Reading: `/agents/crew/run`
- Observability: `/observability/logs`
- Settings: `/settings/public` and `/llm/doctor`

Browser file uploads use `/kb/upload`; the backend accepts PDF, DOCX, PPTX,
Markdown, TXT, and HTML, stores each file in the workspace raw-data area, then
uses the normal indexing pipeline.

The File Organizer and Thesis Check views expose read-safe sibling-module bridge
calls using paths below `personal-agent-workspace/workspace/`. The organizer is
always a dry-run preview and the thesis route is report-only. Keep the API token
in browser-safe development environment configuration only when the FastAPI server
enables token auth.
