"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Command, Search, X } from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { navGroups } from "./navigation";

export function CommandPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [query, setQuery] = useState("");
  const entries = useMemo(() => navGroups.flatMap((group) => group.items).filter((item) => item.label.toLowerCase().includes(query.toLowerCase())), [query]);
  useEffect(() => { if (!open) setQuery(""); }, [open]);
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="top-[18%] max-w-xl p-0"><DialogTitle className="sr-only">Command palette</DialogTitle><div className="flex items-center gap-2 border-b px-4"><Search size={17} className="text-muted-foreground"/><Input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} className="border-0 px-0 shadow-none focus-visible:ring-0" placeholder="Jump to a workspace view..."/><Command size={15} className="text-muted-foreground"/></div><div className="max-h-80 overflow-auto p-2">{entries.map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={() => onOpenChange(false)} className="flex min-h-11 items-center gap-3 rounded-md px-3 text-sm hover:bg-accent"><Icon size={16}/>{label}</Link>)}{!entries.length && <p className="p-4 text-sm text-muted-foreground">No matching views.</p>}</div></DialogContent></Dialog>;
}
