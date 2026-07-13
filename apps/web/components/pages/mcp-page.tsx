"use client";

import { useQuery } from "@tanstack/react-query";
import { Network } from "lucide-react";
import { Panel } from "@/components/shared/panel";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { api } from "@/lib/api";

export function McpPage() {
  const doctor = useQuery({ queryKey: ["mcp-doctor"], queryFn: () => api<{ result: Record<string, unknown> }>("/integrations/mcp/doctor") });
  const result = doctor.data?.result;
  const count = (key: string) => Array.isArray(result?.[key]) ? result[key].length : "-";
  const config = '{\n  "mcpServers": {\n    "scholarmind": {\n      "command": "python",\n      "args": ["-m", "src.cli", "serve"]\n    }\n  }\n}';
  return <div className="grid gap-4 xl:grid-cols-2"><Panel title="Official MCP SDK" eyebrow="Gateway health">{doctor.isPending ? <LoadingSkeleton rows={3}/> : <><div className="grid grid-cols-3 gap-3"><Metric label="Tools" value={count("tools")}/><Metric label="Resources" value={count("resources")}/><Metric label="Prompts" value={count("prompts")}/></div><pre className="mt-5 max-h-72 overflow-auto whitespace-pre-wrap break-words rounded bg-muted/40 p-3 text-xs">{result ? JSON.stringify(result, null, 2) : "MCP doctor unavailable."}</pre></>}</Panel><Panel title="Client configuration" eyebrow="Environment first"><p className="mb-4 text-sm leading-6 text-muted-foreground">Keep API tokens in environment variables rather than MCP client configuration files.</p><pre className="overflow-auto rounded bg-muted/40 p-4 text-xs leading-5">{config}</pre></Panel></div>;
}

function Metric({ label, value }: { label: string; value: number | string }) { return <div className="rounded-md border bg-muted/30 p-4 text-center"><Network className="mx-auto mb-2 text-emerald-400" size={16}/><p className="font-mono text-xl font-semibold">{value}</p><p className="text-xs text-muted-foreground">{label}</p></div>; }
