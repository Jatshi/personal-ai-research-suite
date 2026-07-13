"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

type State = { failed: boolean };
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { failed: false };
  static getDerivedStateFromError(): State { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) {}
  render() {
    if (this.state.failed) return <main className="grid min-h-screen place-items-center bg-background p-6"><section className="max-w-md rounded-lg border border-border bg-card p-8 text-center shadow-lg"><AlertTriangle className="mx-auto mb-4 text-amber-400" size={32}/><h1 className="text-xl font-semibold">Workspace view failed to load</h1><p className="mt-2 text-sm text-muted-foreground">No server-side data has been changed. Reload this view to continue.</p><Button className="mt-6" onClick={() => this.setState({ failed: false })}><RefreshCw/> Try again</Button></section></main>;
    return this.props.children;
  }
}
