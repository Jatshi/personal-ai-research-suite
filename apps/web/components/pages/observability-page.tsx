"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Panel } from "@/components/shared/panel";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { api } from "@/lib/api";
import type { LogEvent } from "@/lib/types";

export function ObservabilityPage() { const [category, setCategory] = useState("rag"); const events = useQuery({ queryKey: ["logs", category], queryFn: () => api<{ events: LogEvent[] }>(`/observability/logs?category=${category}&limit=50`) }); return <div className="space-y-4"><Panel title="Runtime observability" eyebrow="JSONL audit stream"><Tabs value={category} onValueChange={setCategory}><TabsList className="flex-wrap"><TabsTrigger value="rag">RAG</TabsTrigger><TabsTrigger value="tool">Tools</TabsTrigger><TabsTrigger value="agent">Agent</TabsTrigger><TabsTrigger value="multi_agent">Multi-agent</TabsTrigger><TabsTrigger value="evaluation">Evaluation</TabsTrigger></TabsList></Tabs><p className="mt-4 text-sm text-muted-foreground">Events are read-only. Sensitive provider data is excluded from browser responses.</p></Panel><Panel title="Recent events" eyebrow={category}>{events.isPending ? <LoadingSkeleton rows={5}/> : events.isError ? <EmptyState title="Logs unavailable" detail="Check API connectivity or choose another category."/> : events.data?.events.length ? <div className="divide-y">{events.data.events.map((event, index) => <details key={`${event.trace_id ?? event.timestamp}-${index}`} className="py-3"><summary className="cursor-pointer text-sm"><b>{event.query ?? event.goal ?? event.category}</b><span className="float-right text-xs text-muted-foreground">{event.timestamp ?? "No timestamp"}</span></summary><pre className="mt-3 overflow-auto whitespace-pre-wrap break-words rounded bg-muted/40 p-3 text-xs">{JSON.stringify(event, null, 2)}</pre></details>)}</div> : <EmptyState title="No events found" detail="Run a retrieval, agent, or evaluation request to populate this category." icon={Activity}/>}</Panel></div>; }
