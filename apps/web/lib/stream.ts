"use client";

import { useCallback, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";

type StreamEvent<T> = { event: string; data: T | string };
type StreamState<T> = { data: T | null; error: string | null; isStreaming: boolean; token: string };

function parseEvent<T>(block: string): StreamEvent<T> | null {
  const event = block.match(/^event:\s*(.+)$/m)?.[1]?.trim() ?? "message";
  const raw = block.match(/^data:\s*(.+)$/m)?.[1];
  if (!raw) return null;
  try { return { event, data: JSON.parse(raw) as T }; } catch { return { event, data: raw }; }
}

export function useStreamQuery<T>() {
  const controllerRef = useRef<AbortController | null>(null);
  const [state, setState] = useState<StreamState<T>>({ data: null, error: null, isStreaming: false, token: "" });

  const stop = useCallback(() => controllerRef.current?.abort(), []);
  const run = useCallback(async (path: string, payload: unknown) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ data: null, error: null, isStreaming: true, token: "" });
    try {
      const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
      const response = await fetch(`${API_BASE}${path}`, {
        method: "POST", signal: controller.signal,
        headers: { "Content-Type": "application/json", ...(token ? { "X-API-Key": token } : {}) },
        body: JSON.stringify(payload),
      });
      if (!response.ok || !response.body) throw new Error((await response.text()).slice(0, 500) || `Request failed (${response.status})`);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let result: T | null = null;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split(/\r?\n\r?\n/);
        buffer = blocks.pop() ?? "";
        for (const block of blocks) {
          const parsed = parseEvent<T>(block);
          if (!parsed) continue;
          if (parsed.event === "token" && typeof parsed.data === "string") setState((current) => ({ ...current, token: current.token + parsed.data }));
          if (parsed.event === "error") throw new Error(typeof parsed.data === "string" ? parsed.data : "The stream returned an error.");
          if (parsed.event === "result" || parsed.event === "message") {
            if (typeof parsed.data !== "string") { const data = parsed.data as T; result = data; setState((current) => ({ ...current, data })); }
          }
        }
      }
      return result;
    } catch (error) {
      if ((error as Error).name !== "AbortError") setState((current) => ({ ...current, error: error instanceof Error ? error.message : "The stream failed." }));
      return null;
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
      setState((current) => ({ ...current, isStreaming: false }));
    }
  }, []);

  return { ...state, run, stop };
}
