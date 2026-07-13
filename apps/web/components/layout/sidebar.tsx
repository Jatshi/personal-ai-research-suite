"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronsLeft, Cpu, UserRound } from "lucide-react";
import { navGroups } from "./navigation";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();
  return <aside className="hidden w-64 shrink-0 border-r border-border/70 bg-[#10121b] p-3 text-slate-300 lg:flex lg:flex-col"><Link href="/dashboard" className="flex items-center gap-3 px-3 py-3 text-white"><span className="grid size-8 place-items-center rounded-md bg-emerald-400 text-slate-950"><Cpu size={18}/></span><span className="text-sm font-semibold">ScholarMind <small className="block text-[10px] font-normal text-slate-400">AgentOS</small></span></Link><nav className="mt-5 space-y-5">{navGroups.map((group) => <div key={group.label}><p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">{group.label}</p><div className="space-y-0.5">{group.items.map(({ href, label, icon: Icon }) => <Link key={href} href={href} title={label} className={cn("flex min-h-10 items-center gap-3 rounded-md px-3 text-sm transition-colors hover:bg-white/8 hover:text-white", pathname === href && "relative bg-white/10 text-white before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:rounded-full before:bg-emerald-400")}><Icon size={16}/><span>{label}</span></Link>)}</div></div>)}</nav><div className="mt-auto border-t border-white/10 px-3 pt-4"><div className="flex items-center gap-2 text-xs"><UserRound size={18} className="rounded-full bg-slate-700 p-0.5"/><span>Local workspace<small className="block text-[10px] text-emerald-400">Protected mode</small></span><ChevronsLeft size={15} className="ml-auto text-slate-500"/></div></div></aside>;
}
