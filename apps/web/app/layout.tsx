import type { Metadata } from "next";
import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";
import { Providers } from "./providers";
import { ErrorBoundary } from "@/components/shared/error-boundary";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

export const metadata: Metadata = {
  title: "ScholarMind AgentOS",
  description: "Personal AI research operating system",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={cn("dark font-sans", geist.variable)}><body><Providers><ErrorBoundary>{children}</ErrorBoundary></Providers></body></html>;
}
