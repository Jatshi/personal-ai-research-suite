"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity, ArrowUpRight, Bot, BookOpen, CheckCircle2, ChevronRight, Database, FileCheck2,
  Files, FolderInput, GitBranch, LayoutDashboard, ListTree, LoaderCircle, Moon, Network,
  Search, Send, Settings, ShieldCheck, Sparkles, Sun, Wrench,
} from "lucide-react";
import { api, sse, upload } from "@/lib/api";

type Health = { ok: boolean; app: string; llm_backend: string; embedding_backend: string };
type Chunk = { chunk_id?: string; file_name?: string; snippet?: string; text?: string; score?: number; page_number?: number; section_title?: string };
type RagResponse = { answer?: string; confidence?: number; citations?: string[]; evidence?: Chunk[]; results?: Chunk[]; retrieval_trace?: Record<string, unknown>; final_report?: string; steps?: Array<{ tool_name?: string; agent?: string; task?: string; result?: unknown; output?: string }> };
type Dashboard = { documents: number; chunks: number; collections: Array<{ name: string; count: number }>; file_types: Array<{ name: string; count: number }>; graph: { nodes: number; edges: number }; recent_documents: Array<{ doc_id: string; file_name: string; collection: string; file_type: string; imported_at: string; tags?: string[] }> };
type LogEvent = { category: string; timestamp?: string; query?: string; goal?: string; success?: boolean; retrieval_mode?: string; final_report?: string; trace_id?: string; [key: string]: unknown };
type PublicSettings = Record<string, Record<string, unknown>>;

const nav = [
  ["dashboard", "Dashboard", LayoutDashboard], ["import", "Import", FolderInput], ["search", "Search & Ask", Search], ["agent", "AI Assistant", Bot], ["organize", "File Organizer", Files], ["thesis-check", "Thesis Check", FileCheck2], ["paper-reading", "Paper Reading", BookOpen], ["observability", "Observability", Activity], ["mcp", "MCP", Network], ["settings", "Settings", Settings],
] as const;

export function WorkspaceShell({ view }: { view: string }) {
  const [dark, setDark] = useState(true);
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => { api<Health>("/health").then(setHealth).catch(() => setHealth(null)); }, []);
  const title = useMemo(() => nav.find(([id]) => id === view)?.[1] ?? "Dashboard", [view]);
  return <main className={dark ? "app dark" : "app"}>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">S</span><span>ScholarMind</span><small>AgentOS</small></div>
      <nav>{nav.map(([id, label, Icon]) => <Link className={id === view ? "nav-item active" : "nav-item"} href={`/${id}`} key={id}><Icon size={17}/><span>{label}</span></Link>)}</nav>
      <div className="sidebar-foot"><span className={health?.ok ? "status-dot" : "status-dot offline"}/>{health?.ok ? "API connected" : "API offline"}</div>
    </aside>
    <section className="workspace"><header className="topbar"><div><p className="eyebrow">PERSONAL RESEARCH SYSTEM</p><h1>{title}</h1></div><button className="icon-button" title="Toggle theme" onClick={() => setDark(!dark)}>{dark ? <Sun size={18}/> : <Moon size={18}/>}</button></header>
      <ViewRouter view={view} health={health}/>
    </section>
  </main>;
}

function ViewRouter({ view, health }: { view: string; health: Health | null }) {
  if (view === "dashboard") return <DashboardPage health={health}/>;
  if (view === "search") return <SearchPage/>;
  if (view === "agent") return <AgentPage/>;
  if (view === "import") return <ImportPage/>;
  if (view === "paper-reading") return <PaperReadingPage/>;
  if (view === "observability") return <ObservabilityPage/>;
  if (view === "settings") return <SettingsPage/>;
  if (view === "mcp") return <McpPage/>;
  return <CompatibilityPage view={view}/>;
}

function DashboardPage({ health }: { health: Health | null }) {
  const [summary, setSummary] = useState<Dashboard | null>(null);
  useEffect(() => { api<Dashboard>("/dashboard/summary").then(setSummary).catch(() => setSummary(null)); }, []);
  return <div className="page-grid">
    <section className="metrics"><Metric label="Documents" value={summary?.documents?.toString() ?? "-"} note="Indexed local sources" icon={<Database/>}/><Metric label="Chunks" value={summary?.chunks?.toString() ?? "-"} note="Groundable evidence units" icon={<ListTree/>}/><Metric label="Knowledge graph" value={summary ? `${summary.graph.nodes}/${summary.graph.edges}` : "-"} note="Nodes / edges" icon={<GitBranch/>}/><Metric label="LLM provider" value={health?.llm_backend ?? "Offline"} note={health?.ok ? "API is reachable" : "Start FastAPI to connect"} icon={<Bot/>}/></section>
    <section className="dashboard-grid"><article className="panel chart-panel"><PanelTitle eyebrow="KNOWLEDGE BASE" title="Collection distribution"/><div className="distribution">{summary?.collections?.length ? summary.collections.map((item) => <div className="distribution-row" key={item.name}><span>{item.name}</span><div><i style={{ width: `${Math.max(12, item.count / Math.max(...summary.collections.map((x) => x.count)) * 100)}%` }}/></div><b>{item.count}</b></div>) : <Empty text="Import material to create your first collection."/>}</div></article>
      <article className="panel"><PanelTitle eyebrow="RETRIEVAL" title="Evidence-first workflow"/><div className="flow"><span>Ingest</span><ChevronRight/><span>Retrieve</span><ChevronRight/><span>Verify</span><ChevronRight/><span>Answer</span></div><p className="muted">Hybrid retrieval, graph expansion, citation grounding and audit events share one workspace boundary.</p></article></section>
    <section className="panel"><PanelTitle eyebrow="RECENT MATERIAL" title="Recently indexed documents"/>{summary?.recent_documents?.length ? <div className="document-list">{summary.recent_documents.map((doc) => <div className="document-row" key={doc.doc_id}><div><b>{doc.file_name}</b><span>{doc.collection} · {doc.file_type}</span></div><time>{doc.imported_at?.slice(0, 10)}</time></div>)}</div> : <Empty text="No indexed documents yet."/>}</section>
  </div>;
}

function SearchPage() {
  const [query, setQuery] = useState(""); const [mode, setMode] = useState("hybrid"); const [result, setResult] = useState<RagResponse | null>(null); const [busy, setBusy] = useState(false);
  async function run() { if (!query.trim()) return; setBusy(true); try { setResult(await sse<RagResponse>("/rag/ask/stream", { query, mode, top_k: 5 })); } catch (error) { setResult({ answer: message(error) }); } finally { setBusy(false); } }
  const evidence = result?.evidence ?? result?.results ?? [];
  return <div className="ask-layout"><section className="answer-column"><SearchBox value={query} onChange={setQuery} onRun={run} busy={busy} placeholder="Ask your knowledge base..."/><div className="segmented">{["hybrid", "keyword", "semantic", "graphrag"].map((item) => <button className={item === mode ? "selected" : ""} onClick={() => setMode(item)} key={item}>{item}</button>)}</div><section className="panel answer"><PanelTitle eyebrow="GROUNDED ANSWER" title={busy ? "Retrieving evidence" : result ? "Answer" : "Ready"}/><div className="markdown-output">{result?.answer ?? "Ask a question to inspect the answer, citations and retrieval trace."}</div>{result?.confidence !== undefined && <Confidence value={result.confidence}/>}</section></section><aside className="evidence-column"><section className="panel"><PanelTitle eyebrow="RETRIEVAL EVIDENCE" title={`${evidence.length} source chunks`}/>{evidence.length ? evidence.map((item, index) => <details className="evidence" key={item.chunk_id ?? index}><summary><span><b>{item.file_name ?? "Source chunk"}</b><small>{item.section_title || item.page_number ? `${item.section_title ?? ""} ${item.page_number ? `p.${item.page_number}` : ""}` : item.chunk_id}</small></span><em>{Math.round((item.score ?? 0) * 100)}%</em></summary><p>{item.snippet ?? item.text}</p></details>) : <Empty text="Evidence chunks will appear here."/>}</section><section className="panel trace"><PanelTitle eyebrow="RETRIEVAL TRACE" title="Decision record"/><pre>{result?.retrieval_trace ? JSON.stringify(result.retrieval_trace, null, 2) : "No query trace yet."}</pre></section></aside></div>;
}

function AgentPage() {
  const [goal, setGoal] = useState(""); const [result, setResult] = useState<RagResponse | null>(null); const [busy, setBusy] = useState(false);
  async function run() { if (!goal.trim()) return; setBusy(true); try { setResult(await sse<RagResponse>("/agent/chat/stream", { message: goal, mode: "react", session_id: "web-workbench" })); } catch (error) { setResult({ final_report: message(error) }); } finally { setBusy(false); } }
  return <div className="agent-layout"><section className="answer-column"><section className="panel chat-panel"><PanelTitle eyebrow="AI ASSISTANT" title="Plan, retrieve and act with approval"/><div className="chat-message assistant">{result?.final_report ?? "Describe a research task. The assistant will use the configured planner or ReAct loop and preserve dry-run confirmation rules."}</div>{result?.steps?.map((step, index) => <details className="agent-step" key={index}><summary><CheckCircle2 size={15}/><span>{step.agent ?? step.tool_name ?? step.task ?? `Step ${index + 1}`}</span></summary><pre>{JSON.stringify(step.result ?? step.output ?? step, null, 2)}</pre></details>)}<SearchBox value={goal} onChange={setGoal} onRun={run} busy={busy} placeholder="Give ScholarMind a research task..."/></section></section><aside className="evidence-column"><section className="panel"><PanelTitle eyebrow="SAFETY" title="Execution boundary"/><p className="muted">Write operations are planned first. High-risk operations remain dry runs until explicit confirmation is supplied to the backend.</p></section><section className="panel"><PanelTitle eyebrow="SESSION" title="Working memory"/><p className="muted">Session `web-workbench` retains task observations; long-term memory follows the server configuration.</p></section></aside></div>;
}

function ImportPage() {
  const [path, setPath] = useState(""); const [collection, setCollection] = useState("personal"); const [files, setFiles] = useState<File[]>([]); const [result, setResult] = useState<RagResponse | null>(null); const [busy, setBusy] = useState(false);
  async function ingest() { if (!path.trim()) return; setBusy(true); try { setResult(await api<RagResponse>("/kb/ingest", { method: "POST", body: JSON.stringify({ path, collection }) })); } catch (error) { setResult({ answer: message(error) }); } finally { setBusy(false); } }
  async function uploadFiles() { if (!files.length) return; setBusy(true); try { const form = new FormData(); files.forEach((file) => form.append("files", file)); form.append("collection", collection); form.append("tags", "[]"); setResult(await upload<RagResponse>("/kb/upload", form)); setFiles([]); } catch (error) { setResult({ answer: message(error) }); } finally { setBusy(false); } }
  return <div className="form-layout"><section className="panel import-zone"><FolderInput size={34}/><h2>Import a local source</h2><p className="muted">Select supported files for browser upload, or index a file/folder path visible to the local API.</p><label>Collection<input value={collection} onChange={(event) => setCollection(event.target.value)} placeholder="personal"/></label><label>Upload files<input type="file" multiple accept=".pdf,.docx,.pptx,.md,.txt,.html,.htm" onChange={(event) => setFiles(Array.from(event.target.files ?? []))}/></label>{files.length > 0 && <small>{files.length} file(s) selected</small>}<button className="primary wide-button" disabled={busy || !files.length} onClick={uploadFiles}>{busy ? "Uploading..." : "Upload and index"}</button><div className="import-divider">or index a local path</div><label>Source path<input value={path} onChange={(event) => setPath(event.target.value)} placeholder="D:\\research\\papers"/></label><button className="secondary wide-button" disabled={busy || !path.trim()} onClick={ingest}>Index local path</button></section><section className="panel"><PanelTitle eyebrow="IMPORT RESULT" title="Indexing status"/><pre>{result ? JSON.stringify(result, null, 2) : "Choose files or a local path to begin."}</pre></section></div>;
}

function PaperReadingPage() {
  const [topic, setTopic] = useState(""); const [result, setResult] = useState<RagResponse | null>(null); const [busy, setBusy] = useState(false);
  async function runCrew() { if (!topic.trim()) return; setBusy(true); try { setResult(await api<RagResponse>("/agents/crew/run", { method: "POST", body: JSON.stringify({ topic, top_k: 8 }) })); } catch (error) { setResult({ final_report: message(error) }); } finally { setBusy(false); } }
  return <div className="page-grid"><section className="panel command"><PanelTitle eyebrow="FIVE-ROLE CREW" title="Generate an evidence-grounded research note"/><SearchBox value={topic} onChange={setTopic} onRun={runCrew} busy={busy} placeholder="Topic or paper question..."/>{result?.steps?.length ? <div className="crew-steps">{result.steps.map((step, index) => <div key={index}><span>{index + 1}</span><b>{step.agent ?? step.task}</b><small>Completed</small></div>)}</div> : <p className="muted">Reader, Method, Experiment, Critic and Writer use shared retrieved evidence.</p>}</section>{result && <section className="panel"><PanelTitle eyebrow="RESEARCH NOTE" title="Crew synthesis"/><div className="markdown-output">{result.final_report ?? result.answer}</div></section>}</div>;
}

function ObservabilityPage() {
  const [category, setCategory] = useState("rag"); const [events, setEvents] = useState<LogEvent[]>([]); const [error, setError] = useState(""); const [dataset, setDataset] = useState("examples/sample_eval/phase6_rag_eval.jsonl"); const [report, setReport] = useState<Record<string, unknown> | null>(null);
  useEffect(() => { api<{ events: LogEvent[] }>(`/observability/logs?category=${category}&limit=50`).then((value) => { setEvents(value.events); setError(""); }).catch((err) => setError(message(err))); }, [category]);
  async function runEvaluation() { try { setReport(await api<Record<string, unknown>>("/evaluation/run", { method: "POST", body: JSON.stringify({ dataset, engine: "builtin" }) })); setCategory("evaluation"); } catch (err) { setReport({ error: message(err) }); } }
  return <div className="page-grid"><div className="segmented">{["rag", "tool", "agent", "multi_agent", "evaluation"].map((item) => <button key={item} className={item === category ? "selected" : ""} onClick={() => setCategory(item)}>{item.replace("_", " ")}</button>)}</div>{category === "evaluation" && <section className="panel eval-runner"><PanelTitle eyebrow="EVALUATION" title="Run deterministic RAG evaluation"/><div className="query-box"><Search size={17}/><input value={dataset} onChange={(event) => setDataset(event.target.value)} /><button className="primary" onClick={runEvaluation}>Run eval</button></div>{report && <pre>{JSON.stringify(report, null, 2)}</pre>}</section>}<section className="panel"><PanelTitle eyebrow="JSONL OBSERVABILITY" title={`${events.length} recent events`}/>{error ? <p className="error-text">{error}</p> : events.length ? <div className="log-list">{events.map((event, index) => <details key={`${event.trace_id ?? "event"}-${index}`}><summary><span><b>{event.query ?? event.goal ?? event.category}</b><small>{event.timestamp ?? "No timestamp"}</small></span><em>{event.success === false ? "failed" : "recorded"}</em></summary><pre>{JSON.stringify(event, null, 2)}</pre></details>)}</div> : <Empty text="No events recorded for this category."/>}</section></div>;
}

function SettingsPage() {
  const [settings, setSettings] = useState<PublicSettings | null>(null); const [doctor, setDoctor] = useState<Record<string, unknown> | null>(null); const [topK, setTopK] = useState(5); const [crag, setCrag] = useState(false); const [plan, setPlan] = useState<Record<string, unknown> | null>(null); const [busy, setBusy] = useState(false);
  useEffect(() => { api<PublicSettings>("/settings/public").then((value) => { setSettings(value); const retrieval = value.retrieval ?? {}; setTopK(Number(retrieval.top_k ?? 5)); setCrag(Boolean(retrieval.crag_enabled)); }).catch(() => setSettings(null)); }, []);
  async function check() { try { setDoctor(await api<Record<string, unknown>>("/llm/doctor")); } catch (error) { setDoctor({ error: message(error) }); } }
  async function update(confirm = false) { setBusy(true); try { const response = await api<Record<string, unknown>>("/settings/update", { method: "POST", body: JSON.stringify({ changes: { retrieval: { top_k: topK, crag_enabled: crag } }, confirm }) }); setPlan(response); if (confirm) { setSettings(await api<PublicSettings>("/settings/public")); } } catch (error) { setPlan({ error: message(error) }); } finally { setBusy(false); } }
  return <div className="settings-grid">{settings ? Object.entries(settings).filter(([name]) => name !== "success").map(([name, values]) => <section className="panel" key={name}><PanelTitle eyebrow="CONFIGURATION" title={name.replace("_", " ")}/><dl>{Object.entries(values).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{String(value)}</dd></div>)}</dl></section>) : <section className="panel"><Empty text="Unable to load public settings."/></section>}<section className="panel settings-editor"><PanelTitle eyebrow="SAFE EDIT" title="Retrieval controls"/><label>Top K<input type="number" min="1" max="50" value={topK} onChange={(event) => setTopK(Math.max(1, Number(event.target.value)))} /></label><label className="toggle-row"><span>Enable CRAG routing</span><input type="checkbox" checked={crag} onChange={(event) => setCrag(event.target.checked)} /></label><div className="settings-actions"><button className="primary" disabled={busy} onClick={() => update(false)}>Preview changes</button>{plan && !Boolean(plan.executed) && <button className="secondary" disabled={busy} onClick={() => update(true)}>Confirm write</button>}</div>{plan && <pre>{JSON.stringify(plan, null, 2)}</pre>}</section><section className="panel"><PanelTitle eyebrow="CONNECTION" title="Validate configured provider"/><p className="muted">This read-only diagnostic never exposes API keys in the browser.</p><button className="primary" onClick={check}>Run doctor</button>{doctor && <pre>{JSON.stringify(doctor, null, 2)}</pre>}</section></div>;
}

function McpPage() { const [doctor, setDoctor] = useState<Record<string, unknown> | null>(null); const [error, setError] = useState(""); useEffect(() => { api<{ result: Record<string, unknown> }>("/integrations/mcp/doctor").then((value) => setDoctor(value.result)).catch((err) => setError(message(err))); }, []); const tools = Array.isArray(doctor?.tools) ? doctor.tools.length : "-"; const resources = Array.isArray(doctor?.resources) ? doctor.resources.length : "-"; const prompts = Array.isArray(doctor?.prompts) ? doctor.prompts.length : "-"; return <div className="page-grid"><section className="panel"><PanelTitle eyebrow="MCP GATEWAY" title="Official SDK integration"/><p className="muted">{error || "The local MCP toolkit publishes FastMCP tools, resources and prompts through the verified doctor bridge."}</p><div className="mcp-list"><span>Tools: {tools}</span><span>Resources: {resources}</span><span>Prompts: {prompts}</span></div>{doctor && <pre>{JSON.stringify(doctor, null, 2)}</pre>}</section><section className="panel"><PanelTitle eyebrow="CLIENT CONFIGURATION" title="Keep credentials outside configuration files"/><pre>{`{\n  "mcpServers": {\n    "scholarmind": {\n      "command": "python",\n      "args": ["-m", "src.cli", "serve"]\n    }\n  }\n}`}</pre></section></div>; }

function CompatibilityPage({ view }: { view: string }) {
  const [path, setPath] = useState(""); const [result, setResult] = useState<RagResponse | null>(null); const [busy, setBusy] = useState(false);
  const organizing = view === "organize";
  const title = organizing ? "File Organizer" : "Thesis Check";
  const description = organizing
    ? "Create a dry-run organization plan through the Personal Agent Workspace. No rename, move or delete operation is executed by this route."
    : "Run the existing thesis structure and reference checker through the Personal Agent Workspace. It generates reports but never edits the thesis source.";
  async function run() { if (!path.trim()) return; setBusy(true); try { setResult(await api<RagResponse>(`/integrations/agent-workspace/${organizing ? "organize" : "thesis-check"}`, { method: "POST", body: JSON.stringify({ path }) })); } catch (error) { setResult({ answer: message(error) }); } finally { setBusy(false); } }
  return <div className="form-layout"><section className="panel compatibility"><ShieldCheck size={30}/><h2>{title}</h2><p className="muted">{description}</p><label>Path below `personal-agent-workspace`<input value={path} onChange={(event) => setPath(event.target.value)} placeholder={organizing ? "workspace/papers/to-organize" : "workspace/thesis/thesis.md"}/></label><button className="primary wide-button" onClick={run} disabled={busy || !path.trim()}>{busy ? "Checking..." : organizing ? "Preview dry-run plan" : "Run thesis check"}</button><a className="text-link" href="http://127.0.0.1:8501" target="_blank">Open Streamlit workspace <ArrowUpRight size={15}/></a></section><section className="panel"><PanelTitle eyebrow="BRIDGE RESULT" title={organizing ? "Safe operation preview" : "Check report status"}/><pre>{result ? JSON.stringify(result, null, 2) : "Choose a workspace-relative path to begin."}</pre></section></div>;
}

function SearchBox({ value, onChange, onRun, busy, placeholder }: { value: string; onChange: (value: string) => void; onRun: () => void; busy: boolean; placeholder: string }) { return <div className="query-box"><Search size={19}/><input value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={(event) => event.key === "Enter" && onRun()} placeholder={placeholder}/><button className="primary" onClick={onRun} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16}/> : <Send size={16}/>}<span>{busy ? "Working" : "Run"}</span></button></div>; }
function PanelTitle({ eyebrow, title }: { eyebrow: string; title: string }) { return <div className="panel-title"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>; }
function Metric({ label, value, note, icon }: { label: string; value: string; note: string; icon: React.ReactNode }) { return <article className="metric"><div className="metric-icon">{icon}</div><p>{label}</p><h2>{value}</h2><span>{note}</span></article>; }
function Confidence({ value }: { value: number }) { const percentage = Math.max(0, Math.min(100, Math.round(value * 100))); return <div className="confidence"><span>Grounding confidence</span><div><i style={{ width: `${percentage}%` }}/></div><b>{percentage}%</b></div>; }
function Empty({ text }: { text: string }) { return <div className="empty"><Sparkles size={18}/><span>{text}</span></div>; }
function message(error: unknown) { return error instanceof Error ? error.message : "The request could not be completed."; }
