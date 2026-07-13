"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string; createdAt: string; trace?: string[] };
type SearchState = { history: string[]; mode: string; addQuery: (query: string) => void; setMode: (mode: string) => void };
type ChatState = { messages: ChatMessage[]; add: (message: ChatMessage) => void; clear: () => void };

export const useSearchStore = create<SearchState>()(persist((set) => ({
  history: [], mode: "hybrid",
  addQuery: (query) => set((state) => ({ history: [query, ...state.history.filter((item) => item !== query)].slice(0, 10) })),
  setMode: (mode) => set({ mode }),
}), { name: "scholarmind-search" }));

export const useChatStore = create<ChatState>()(persist((set) => ({
  messages: [], add: (message) => set((state) => ({ messages: [...state.messages, message] })), clear: () => set({ messages: [] }),
}), { name: "scholarmind-agent-chat" }));
