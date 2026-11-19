import Sidebar from "@/components/Sidebar";
import type { Metadata } from "next";
import "../globals.css";

export const metadata: Metadata = { title: "ParallaX | Bengaluru Road Safety Intelligence" };

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
        {children}
      </main>
    </div>
  );
}
