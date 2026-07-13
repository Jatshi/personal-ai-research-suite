import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Panel({ title, eyebrow, children, className }: { title?: string; eyebrow?: string; children: ReactNode; className?: string }) {
  return <section className={cn("rounded-lg border border-border/80 bg-card p-5 shadow-sm", className)}>{title && <header className="mb-5"><p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-emerald-400">{eyebrow ?? "Workspace"}</p><h2 className="mt-1 text-base font-semibold tracking-normal">{title}</h2></header>}{children}</section>;
}
