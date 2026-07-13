"use client";

import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";

export function MetricCard({ label, value, note, icon: Icon }: { label: string; value: string | number; note: string; icon: LucideIcon }) {
  return <motion.article initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="min-h-36 rounded-lg border border-border/80 bg-card p-5 shadow-sm"><Icon size={19} className="mb-5 text-emerald-400"/><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-mono text-2xl font-semibold">{value}</p><p className="mt-1 text-xs text-muted-foreground">{note}</p></motion.article>;
}
