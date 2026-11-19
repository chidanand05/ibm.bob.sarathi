"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Overview", icon: "🏠" },
  { href: "/analytics", label: "Accident Analytics", icon: "📊" },
  { href: "/blackspots", label: "Blackspot Intelligence", icon: "📍" },
  { href: "/gismap", label: "Bengaluru GIS Map", icon: "🗺️" },
  { href: "/cas", label: "CAS Alert Analysis", icon: "⚡" },
  { href: "/agents", label: "AI Agents", icon: "🤖" },
  { href: "/recommendations", label: "Safety Recommendations", icon: "🛡️" },
  { href: "/data-sources", label: "Data Sources", icon: "🗄️" },
  { href: "/assistant", label: "AI Assistant", icon: "💬" },
];

const S: Record<string, React.CSSProperties> = {
  sidebar: { width: 220, minHeight: "100vh", background: "#0D1524", borderRight: "1px solid #1e3050", padding: "16px 0", display: "flex", flexDirection: "column" },
  brand: { padding: "0 16px 20px", borderBottom: "1px solid #1e3050", marginBottom: 8 },
  brandTitle: { fontSize: 15, fontWeight: 700, color: "#29C8E8", letterSpacing: "0.05em" },
  brandSub: { fontSize: 11, color: "#64748b", marginTop: 2 },
  link: { display: "flex", alignItems: "center", gap: 10, padding: "9px 16px", fontSize: 13, color: "#94A3B8", textDecoration: "none", transition: "all 0.15s", borderLeft: "3px solid transparent" },
  active: { color: "#29C8E8", background: "#0f1e35", borderLeft: "3px solid #29C8E8" },
};

export default function Sidebar() {
  const path = usePathname();
  return (
    <nav style={S.sidebar}>
      <div style={S.brand}>
        <div style={S.brandTitle}>PARALLAX</div>
        <div style={S.brandSub}>Road Safety Intelligence</div>
        <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>Bengaluru · PS-8 · IBM Hackathon</div>
      </div>
      {NAV.map(n => (
        <Link key={n.href} href={n.href} style={{ ...S.link, ...(path === n.href ? S.active : {}) }}>
          <span style={{ fontSize: 14 }}>{n.icon}</span>
          <span>{n.label}</span>
        </Link>
      ))}
    </nav>
  );
}
