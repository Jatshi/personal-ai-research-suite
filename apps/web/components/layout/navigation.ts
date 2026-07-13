import { Activity, Bot, Database, FileCheck2, Files, FolderInput, LayoutDashboard, Network, Search, Settings, Wrench, type LucideIcon } from "lucide-react";

export type NavItem = { href: string; label: string; icon: LucideIcon };
export const navGroups: Array<{ label: string; items: NavItem[] }> = [
  { label: "Workspace", items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }, { href: "/import", label: "Import", icon: FolderInput }, { href: "/search", label: "Search", icon: Search }, { href: "/agent", label: "Agent", icon: Bot }] },
  { label: "Research tools", items: [{ href: "/paper-reading", label: "Paper Reading", icon: Files }, { href: "/thesis-check", label: "Thesis Check", icon: FileCheck2 }, { href: "/organize", label: "File Organizer", icon: Wrench }] },
  { label: "System", items: [{ href: "/observability", label: "Observability", icon: Activity }, { href: "/mcp", label: "MCP", icon: Network }, { href: "/settings", label: "Settings", icon: Settings }] },
];

export const pageTitles: Record<string, string> = Object.fromEntries(navGroups.flatMap((group) => group.items.map((item) => [item.href.slice(1), item.label])));
