import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ParallaX | Bengaluru Road Safety Intelligence",
  description: "AI-Powered Urban Accident Analytics & Blackspot Intelligence — Team ParallaX",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#080D18", color: "#e2e8f0", minHeight: "100vh" }}>
        {children}
      </body>
    </html>
  );
}
