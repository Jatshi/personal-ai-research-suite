"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MoreHorizontal } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { navGroups } from "./navigation";
import { cn } from "@/lib/utils";

const main = navGroups[0].items.filter((item) => ["/dashboard", "/search", "/agent"].includes(item.href));
export function MobileNav() { const pathname = usePathname(); return <div className="fixed inset-x-0 bottom-0 z-30 flex h-16 border-t bg-background/95 px-2 backdrop-blur lg:hidden">{main.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={cn("grid flex-1 place-items-center gap-0.5 text-[10px] text-muted-foreground", pathname === href && "text-emerald-400")}><Icon size={19}/>{label}</Link>)}<Sheet><SheetTrigger className="grid flex-1 place-items-center gap-0.5 text-[10px] text-muted-foreground"><MoreHorizontal size={20}/>More</SheetTrigger><SheetContent side="bottom" className="rounded-t-xl"><div className="grid grid-cols-2 gap-2 pt-4">{navGroups.slice(1).flatMap((group) => group.items).map(({ href, label, icon: Icon }) => <Link key={href} href={href} className="flex min-h-12 items-center gap-2 rounded-md border p-3 text-sm"><Icon size={16}/>{label}</Link>)}</div></SheetContent></Sheet></div>; }
