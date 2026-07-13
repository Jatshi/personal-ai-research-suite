"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { CommandPalette } from "@/components/layout/command-palette";
import { MobileNav } from "@/components/layout/mobile-nav";
import { pageTitles } from "@/components/layout/navigation";
import { DashboardPage } from "@/components/pages/dashboard-page";
import { SearchPage } from "@/components/pages/search-page";
import { AgentPage } from "@/components/pages/agent-page";
import { ImportPage } from "@/components/pages/import-page";
import { PaperReadingPage } from "@/components/pages/paper-reading-page";
import { CompatibilityPage } from "@/components/pages/compatibility-page";
import { ObservabilityPage } from "@/components/pages/observability-page";
import { McpPage } from "@/components/pages/mcp-page";
import { SettingsPage } from "@/components/pages/settings-page";

function View({ view }: { view: string }) {
  if (view === "import") return <ImportPage/>;
  if (view === "search") return <SearchPage/>;
  if (view === "agent") return <AgentPage/>;
  if (view === "organize" || view === "thesis-check") return <CompatibilityPage view={view}/>;
  if (view === "paper-reading") return <PaperReadingPage/>;
  if (view === "observability") return <ObservabilityPage/>;
  if (view === "mcp") return <McpPage/>;
  if (view === "settings") return <SettingsPage/>;
  return <DashboardPage/>;
}

export function WorkspaceShell({ view }: { view: string }) {
  const [commandOpen, setCommandOpen] = useState(false);
  const [dark, setDark] = useState(true);
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setCommandOpen(true); }
      if (event.key === "Escape") setCommandOpen(false);
    };
    window.addEventListener("keydown", onKeyDown); return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  return <div className="min-h-screen bg-background"><div className="mx-auto flex min-h-screen max-w-[1800px]"><Sidebar/><main className="min-w-0 flex-1 px-4 pb-24 pt-6 sm:px-7 lg:px-10 lg:pb-10"><Topbar title={pageTitles[view] ?? "Dashboard"} onCommand={() => setCommandOpen(true)} dark={dark} onTheme={() => setDark((value) => !value)}/><AnimatePresence mode="wait"><motion.div key={view} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.2 }}><View view={view}/></motion.div></AnimatePresence></main></div><MobileNav/><CommandPalette open={commandOpen} onOpenChange={setCommandOpen}/></div>;
}
