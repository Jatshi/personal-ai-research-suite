import { Sparkles, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EmptyState({ title, detail, action, icon: Icon = Sparkles }: { title: string; detail: string; action?: { label: string; onClick: () => void }; icon?: LucideIcon }) {
  return <div className="grid min-h-44 place-items-center rounded-lg border border-dashed border-border bg-muted/30 p-6 text-center"><div><Icon className="mx-auto mb-3 text-emerald-400" size={25}/><h3 className="text-sm font-semibold">{title}</h3><p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">{detail}</p>{action && <Button variant="outline" size="sm" className="mt-4" onClick={action.onClick}>{action.label}</Button>}</div></div>;
}
