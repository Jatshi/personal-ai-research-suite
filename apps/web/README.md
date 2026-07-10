# ScholarMind Web

The Phase 6G Next.js workbench is a parallel UI for the existing Streamlit app.

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

It consumes FastAPI REST and SSE endpoints. Keep the API token in browser-safe
development environment configuration only when the FastAPI server enables token auth.
