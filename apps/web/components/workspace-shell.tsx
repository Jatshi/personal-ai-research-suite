"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, Bot, BookOpen, Database, FileCheck2, Files, FolderInput, GitBranch, LayoutDashboard, Moon, Network, Search, Settings, Sun, Wrench } from "lucide-react";
import { api, sse } from "@/lib/api";

type Health = { ok: boolean; app: string; llm_backend: string; embedding_backend: string };
type SearchResult = { answer?: string; confidence?: number; citations?: string[]; evidence?: Array<{ file_name: string; snippet?: string; score?: number }>; retrieval_trace?: Record<string, unknown>; final_report?: string; steps?: Array<{ tool_name: string; result: unknown }> };

const nav = [
  ["dashboard", "Dashboard", LayoutDashboard], ["import", "Import", FolderInput], ["search", "Search & Ask", Search], ["agent", "AI Assistant", Bot], ["organize", "File Organizer", Files], ["thesis-check", "Thesis Check", FileCheck2], ["paper-reading", "Paper Reading", BookOpen], ["observability", "Observability", Activity], ["mcp", "MCP", Network], ["settings", "Settings", Settings],
] as const;

export function WorkspaceShell({ view }: { view: string }) {
  const [dark, setDark] = useState(true);
  const [health, setHealth] = useState<Health | null>(null);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api<Health>("/health").then(setHealth).catch(() => setHealth(null)); }, []);
  const title = useMemo(() => nav.find(([id]) => id === view)?.[1] ?? "Dashboard", [view]);
  async function run() {
    if (!query.trim()) return;
    setBusy(true);
    try {
      const path = view === "agent" ? "/agent/chat/stream" : "/rag/ask/stream";
      setResult(await sse<SearchResult>(path, view === "agent" ? { message: query, mode: "react" } : { query, top_k: 5 }));
    } finally { setBusy(false); }
  }
  async function runWorkflow() {
    setBusy(true);
    try {
      const endpoint = view === "import" ? "/kb/ingest" : view === "paper-reading" ? "/agents/crew/run" : view === "observability" ? "/observability/logs" : view === "settings" ? "/llm/doctor" : "/health";
      const init = view === "import"
        ? { method: "POST", body: JSON.stringify({ path: query, collection: "personal" }) }
        : view === "paper-reading"
          ? { method: "POST", body: JSON.stringify({ topic: query, top_k: 8 }) }
          : undefined;
      setResult(await api<SearchResult>(endpoint, init));
    } catch (error) {
      setResult({ answer: error instanceof Error ? error.message : "Workflow failed." });
    } finally { setBusy(false); }
  }
  return <main className={dark ? "app dark" : "app"}>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">S</span><span>ScholarMind</span><small>AgentOS</small></div>
      <nav>{nav.map(([id, label, Icon]) => <Link className={id === view ? "nav-item active" : "nav-item"} href={`/${id}`} key={id}><Icon size={17}/><span>{label}</span></Link>)}</nav>
      <div className="sidebar-foot"><span className="status-dot"/> API {health?.ok ? "connected" : "offline"}</div>
    </aside>
    <section className="workspace"><header className="topbar"><div><p className="eyebrow">PERSONAL RESEARCH SYSTEM</p><h1>{title}</h1></div><button className="icon-button" title="Toggle theme" onClick={() => setDark(!dark)}>{dark ? <Sun size={18}/> : <Moon size={18}/>}</button></header>
      {view === "dashboard" ? <Dashboard health={health}/> : <WorkPanel view={view} query={query} setQuery={setQuery} run={run} runWorkflow={runWorkflow} result={result} busy={busy}/>}</section>
  </main>;
}

function Dashboard({ health }: { health: Health | null }) {
  return <div className="page-grid"><section className="metrics"><Metric label="Knowledge Base" value="Local" note="Grounded retrieval enabled" icon={<Database/>}/><Metric label="LLM Provider" value={health?.llm_backend ?? "Offline"} note="OpenAI compatible" icon={<Bot/>}/><Metric label="Retrieval" value="Hybrid + Graph" note="Traceable evidence" icon={<GitBranch/>}/><Metric label="Safety" value="Dry-run" note="Approval required for writes" icon={<Wrench/>}/></section>
    <section className="analytics"><div className="panel wide"><p className="eyebrow">RESEARCH ACTIVITY</p><h2>Query and evidence flow</h2><div className="spark"><i/><i/><i/><i/><i/><i/><i/></div></div><div className="panel"><p className="eyebrow">SYSTEM HEALTH</p><h2>{health?.ok ? "Operational" : "Awaiting API"}</h2><p className="muted">LLM and embedding backends are shown from the live FastAPI health endpoint.</p></div></section>
    <section className="panel"><p className="eyebrow">OPERATING PRINCIPLE</p><h2>Evidence before action</h2><p className="muted">Search, citations, agent tools, memory, GraphRAG and MCP share one local audit boundary.</p></section></div>;
}

function WorkPanel({ view, query, setQuery, run, runWorkflow, result, busy }: { view: string; query: string; setQuery: (value: string) => void; run: () => void; runWorkflow: () => void; result: SearchResult | null; busy: boolean }) {
  const interactive = view === "search" || view === "agent";
  const labels: Record<string, string> = { import: "Import documents into a collection", organize: "Preview safe file organization plans", "thesis-check": "Inspect thesis structure and references", "paper-reading": "Run the five-role research crew", observability: "Review query, tool and agent traces", mcp: "Inspect the official MCP server", settings: "Configure API-backed workspace behavior" };
  if (!interactive) {
    const apiReady = ["import", "paper-reading", "observability", "mcp", "settings"].includes(view);
    const placeholder = view === "import" ? "Absolute path within the workspace..." : view === "paper-reading" ? "Research topic for the five-role crew..." : "";
    return <div className="page-grid"><section className="panel command"><p className="eyebrow">{view.toUpperCase()}</p><h2>{labels[view]}</h2>{apiReady && <div className="query-box"><Search size={19}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={placeholder}/><button className="primary" disabled={busy || ((view === "import" || view === "paper-reading") && !query.trim())} onClick={runWorkflow}>{busy ? "Working" : "Run"}</button></div>}{!apiReady && <p className="muted">This workflow remains available in the compatibility Streamlit application while its safe operation API is migrated to this interface.</p>}{result && <pre>{JSON.stringify(result, null, 2)}</pre>}</section></div>;
  }
  return <div className="ask-layout"><section className="answer-column"><div className="query-box"><Search size={19}/><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && run()} placeholder={view === "agent" ? "Give ScholarMind a research task..." : "Ask your knowledge base..."}/><button className="primary" onClick={run} disabled={busy}>{busy ? "Working" : "Run"}</button></div>
    <section className="panel answer"><p className="eyebrow">{view === "agent" ? "AGENT RESPONSE" : "GROUNDED ANSWER"}</p><h2>{busy ? "Working through evidence" : result ? "Result" : "Ready"}</h2><pre>{result?.answer ?? result?.final_report ?? "Ask a question to inspect answers, citations, agent steps and retrieval traces."}</pre>{result?.confidence !== undefined && <div className="confidence"><span>Confidence</span><b>{Math.round(result.confidence * 100)}%</b></div>}</section></section>
    <aside className="evidence-column"><section className="panel"><p className="eyebrow">EVIDENCE</p>{result?.evidence?.length ? result.evidence.map((item, index) => <article className="evidence" key={`${item.file_name}-${index}`}><b>{item.file_name}</b><span>{item.snippet ?? "Source chunk"}</span></article>) : <p className="muted">Retrieved chunks and citations appear here.</p>}</section><section className="panel"><p className="eyebrow">TRACE</p><pre>{result?.retrieval_trace ? JSON.stringify(result.retrieval_trace, null, 2) : "Retrieval and tool traces are available after a run."}</pre></section></aside></div>;
}

function Metric({ label, value, note, icon }: { label: string; value: string; note: string; icon: React.ReactNode }) { return <article className="metric"><div className="metric-icon">{icon}</div><p>{label}</p><h2>{value}</h2><span>{note}</span></article>; }
