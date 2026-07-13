"use client";

import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { Database, FileText, GitBranch, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { MetricCard } from "@/components/shared/metric-card";
import { Panel } from "@/components/shared/panel";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";

export function DashboardPage() {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dashboard>("/dashboard/summary") });
  if (dashboard.isPending) return <LoadingSkeleton rows={8}/>;
  if (dashboard.isError || !dashboard.data) return <EmptyState title="Dashboard unavailable" detail="The API summary could not be loaded. Check the local API connection."/>;
  const data = dashboard.data;
  return <div className="space-y-4"><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><MetricCard label="Documents" value={data.documents} note="Indexed source files" icon={FileText}/><MetricCard label="Evidence chunks" value={data.chunks} note="Traceable retrieval units" icon={Database}/><MetricCard label="Graph relationships" value={data.graph.edges} note={`${data.graph.nodes} entities indexed`} icon={GitBranch}/><MetricCard label="Grounded queries" value={data.queries.total} note={`${Math.round((data.queries.average_confidence ?? 0) * 100)}% average confidence`} icon={Search}/></div><div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]"><Panel title="Query activity" eyebrow="Observability" className="min-h-64"><ResponsiveContainer width="100%" height={190}><AreaChart data={data.queries.trend}><defs><linearGradient id="queryFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#34d399" stopOpacity={0.4}/><stop offset="1" stopColor="#34d399" stopOpacity={0}/></linearGradient></defs><XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={11}/><Tooltip/><Area type="monotone" dataKey="count" stroke="#34d399" fill="url(#queryFill)" strokeWidth={2}/></AreaChart></ResponsiveContainer></Panel><Panel title="Collections" eyebrow="Knowledge base"><div className="space-y-3">{data.collections.length ? data.collections.map((item) => <div key={item.name} className="flex items-center justify-between text-sm"><span>{item.name}</span><span className="font-mono text-muted-foreground">{item.count}</span></div>) : <EmptyState title="No collections" detail="Import documents to start building the knowledge base."/>}</div></Panel></div><Panel title="Recent documents" eyebrow="Index"><div className="divide-y">{data.recent_documents.length ? data.recent_documents.slice(0, 8).map((doc) => <div key={doc.doc_id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"><div><p className="font-medium">{doc.file_name}</p><p className="text-xs text-muted-foreground">{doc.collection} · {doc.file_type}</p></div><time className="text-xs text-muted-foreground">{doc.imported_at}</time></div>) : <EmptyState title="No documents yet" detail="Use Import to create the first collection."/>}</div></Panel></div>;
}
