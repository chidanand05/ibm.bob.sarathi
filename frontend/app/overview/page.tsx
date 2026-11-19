"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 20, marginBottom: 16 } as React.CSSProperties };

function KPICard({ label, value, sub, color }: { label: string; value: any; sub?: string; color?: string }) {
  return (
    <div style={{ ...C.card, flex: 1, minWidth: 140, textAlign: "center" }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || "#29C8E8" }}>{value ?? "—"}</div>
      <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export default function OverviewPage() {
  const [summary, setSummary] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [topStations, setTopStations] = useState<any[]>([]);
  const [zones, setZones] = useState<any[]>([]);
  const [agentStatus, setAgentStatus] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.summary().catch(() => null),
      api.annualTrends().catch(() => ({ data: [] })),
      api.byStation().catch(() => ({ data: [] })),
      api.agents().catch(() => ({ agents: [] })),
    ]).then(([s, t, st, ag]) => {
      setSummary(s);
      setTrends((t?.data || []).slice(-10));
      setTopStations((st?.data || []).slice(0, 10));
      setAgentStatus(ag?.agents || []);
      setLoading(false);
    });
  }, []);

  if (loading) return <Layout><div style={{ color: "#29C8E8", padding: 40 }}>Loading dashboard…</div></Layout>;

  const yr = summary?.latest_year || 2024;

  return (
    <Layout>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "#e2e8f0", margin: 0 }}>Bengaluru Road Safety Intelligence</h1>
        <p style={{ color: "#64748b", marginTop: 4, fontSize: 13 }}>
          AI-Powered Urban Accident Analytics &amp; Blackspot Intelligence · Team ParallaX · IBM Hackathon PS-8
        </p>
      </div>

      {/* KPI Row */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
        <KPICard label="Total Accidents" value={summary?.total_accidents?.toLocaleString()} sub={`Year ${yr}`} color="#29C8E8" />
        <KPICard label="Fatal Accidents" value={summary?.fatal_accidents?.toLocaleString()} color="#EF5350" />
        <KPICard label="Non-Fatal" value={summary?.non_fatal_accidents?.toLocaleString()} color="#F59E0B" />
        <KPICard label="People Killed" value={summary?.people_killed?.toLocaleString()} color="#EF5350" />
        <KPICard label="People Injured" value={summary?.people_injured?.toLocaleString()} color="#F59E0B" />
        <KPICard label="Official BTP Blackspots" value={summary?.official_blackspots} color="#29C8E8" />
        <KPICard label="CAS Alert Records" value={summary?.cas_alert_records?.toLocaleString()} sub="Feb–Jul 2018" color="#94A3B8" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        {/* Trend Chart */}
        <div style={C.card}>
          <h3 style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Annual Accident Trend (2015–2025)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3050" />
              <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", borderRadius: 6, fontSize: 12 }} />
              <Line type="monotone" dataKey="total_accidents" stroke="#29C8E8" dot={false} strokeWidth={2} name="Total" />
              <Line type="monotone" dataKey="fatal_accidents" stroke="#EF5350" dot={false} strokeWidth={2} name="Fatal" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Stations Bar */}
        <div style={C.card}>
          <h3 style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Top Stations by Accidents ({yr})</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={topStations} layout="vertical" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3050" horizontal={false} />
              <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="police_station" stroke="#64748b" tick={{ fontSize: 10 }} width={80} />
              <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", fontSize: 12 }} />
              <Bar dataKey="total_accidents" fill="#29C8E8" name="Total" radius={[0, 4, 4, 0]} />
              <Bar dataKey="fatal_accidents" fill="#EF5350" name="Fatal" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent Status */}
      <div style={C.card}>
        <h3 style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600, marginBottom: 12 }}>AI Agent Status</h3>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {agentStatus.map((ag: any) => (
            <div key={ag.id} style={{ background: "#0D1524", border: "1px solid #1e3050", borderRadius: 8, padding: "10px 14px", minWidth: 180 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: ag.status === "active" ? "#22C55E" : "#F59E0B", display: "inline-block" }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{ag.name.replace("Agent", "").trim()}</span>
              </div>
              <div style={{ fontSize: 11, color: "#64748b" }}>{ag.status === "active" ? "Active" : "Awaiting Data"}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Notice */}
      <div style={{ ...C.card, background: "#0a1520", borderColor: "#29C8E8", borderLeftWidth: 4 }}>
        <p style={{ fontSize: 12, color: "#94A3B8", margin: 0 }}>
          <strong style={{ color: "#29C8E8" }}>Data Sources:</strong> 5 Historical Accident CSV Datasets (2018–2024) · 1 CAS Alert Dataset (207,575 records, Feb–Jul 2018) · 64 Official BTP Blackspot Locations.{" "}
          CAS alerts are driving-safety indicators, not confirmed accidents. All metrics derived from actual datasets.
        </p>
      </div>
    </Layout>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 24, overflowY: "auto" }}>{children}</main>
    </div>
  );
}
