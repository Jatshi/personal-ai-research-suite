import { WorkspaceShell } from "@/components/workspace-shell";

const views = new Set(["dashboard", "import", "search", "agent", "organize", "thesis-check", "paper-reading", "observability", "mcp", "settings"]);

export function generateStaticParams() {
  return [...views].map((view) => ({ view }));
}

export default async function WorkspaceView({ params }: { params: Promise<{ view: string }> }) {
  const { view } = await params;
  return <WorkspaceShell view={views.has(view) ? view : "dashboard"} />;
}
