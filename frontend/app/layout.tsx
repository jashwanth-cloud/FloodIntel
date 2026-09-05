import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "FloodIntel | Flood Intelligence", description: "AI-powered flood intelligence and early warning platform" };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body><div className="min-h-screen bg-[#061423] text-slate-100">{children}</div></body></html>; }
