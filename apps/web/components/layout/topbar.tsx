"use client";

import { Command, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Topbar({ title, onCommand, dark, onTheme }: { title: string; onCommand: () => void; dark: boolean; onTheme: () => void }) {
  return <header className="mb-7 flex items-start justify-between gap-4"><div><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-emerald-400">Research operating system</p><h1 className="mt-1 text-2xl font-semibold tracking-normal sm:text-[29px]">{title}</h1></div><div className="flex items-center gap-2"><span className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-400 sm:flex"><i className="size-1.5 rounded-full bg-current"/>System online</span><Button variant="outline" size="sm" className="hidden text-muted-foreground sm:flex" onClick={onCommand}><Command size={14}/> Command <kbd className="rounded border bg-muted px-1 text-[10px]">Ctrl K</kbd></Button><Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={onTheme}>{dark ? <Sun size={18}/> : <Moon size={18}/>}</Button></div></header>;
}
