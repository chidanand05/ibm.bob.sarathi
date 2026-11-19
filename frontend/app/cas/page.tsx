"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 16, marginBottom: 12 } as React.CSSProperties };
const COLORS = ["#29C8E8", "#EF5350", "#F59E0B", "#22C55E", "#a855f7", "#ec4899", "#14b8a6"];

export default function CASPage() {
  const [summary, setSummary] = useState<any>(null);
  const [wards, setWards] = useState<any[]>([]);
  const [overspeed, setOverspeed] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      api.casSummary().catch(() => null),
      api.casByWard().catch(() => ({ data: [] })),
      api.casOverspeed().catch(() => null),
    ]).then(([s, w, o]) => { setSummary(s); setWards(w.data || []); setOverspeed(o); });
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 24, overflowY: "auto" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>CAS Alert Analysis</h1>
        <div style={{ background: "#0a1520", border: "1px solid #F59E0B", borderLeftWidth: 4, borderRadius: 6, padding: "10px 14px", marginBottom: 16, fontSize: 11, color: "#94A3B8" }}>
          <b style={{ color: "#F59E0B" }}>DATA NOTE:</b> CAS records are <b>Collision Avoidance System driving-safety alerts</b> (Feb–Jul 2018).
          They are NOT confirmed accidents. Alert counts do not directly represent accident probability.
          Used as supplementary driving-behavior indicators only.
        </div>

        {summary && (
          <>
            <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
              {[
                { label: "Total CAS Alerts", val: summary.total_alerts?.toLocaleString(), c: "#F59E0B" },
                { label: "Alarm Types", val: summary.alarm_distribution?.length, c: "#29C8E8" },
                { label: "Unique Wards", val: summary.top_wards?.length, c: "#29C8E8" },
                { label: "Overspeed Alerts", val: overspeed?.total_overspeed_alerts?.toLocaleString(), c: "#EF5350" },
              ].map(k => (
                <div key={k.label} style={{ ...C.card, flex: 1, minWidth: 140, textAlign: "center", marginBottom: 0 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: k.c }}>{k.val ?? "—"}</div>
                  <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 4 }}>{k.label}</div>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <div style={C.card}>
                <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Alert Type Distribution</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={summary.alarm_distribution} dataKey="count" nameKey="alarm_type" cx="50%" cy="50%" outerRadius={80}
                      label={({ alarm_type, percent }: any) => `${alarm_type} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                      {summary.alarm_distribution.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={C.card}>
                <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Top Wards by Alert Count</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={summary.top_wards?.slice(0, 12)} layout="vertical" margin={{ left: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e3050" horizontal={false} />
                    <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis type="category" dataKey="ward" stroke="#64748b" tick={{ fontSize: 9 }} width={80} />
                    <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", fontSize: 12 }} />
                    <Bar dataKey="total_alerts" fill="#F59E0B" name="Total Alerts" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="overspeed_alerts" fill="#EF5350" name="Overspeed" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}

        <div style={C.card}>
          <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Ward-Level Alert Breakdown</h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead><tr style={{ borderBottom: "1px solid #1e3050" }}>
                {["#", "Ward", "Total Alerts", "Overspeed", "Avg Speed"].map(h =>
                  <th key={h} style={{ padding: "7px 10px", textAlign: "left", color: "#64748b" }}>{h}</th>)}
              </tr></thead>
              <tbody>
                {wards.map((r: any, i: number) => (
                  <tr key={r.ward} style={{ borderBottom: "1px solid #0f1a2a" }}>
                    <td style={{ padding: "6px 10px", color: "#64748b" }}>{i + 1}</td>
                    <td style={{ padding: "6px 10px", color: "#e2e8f0" }}>{r.ward}</td>
                    <td style={{ padding: "6px 10px", color: "#F59E0B", fontWeight: 600 }}>{r.total_alerts?.toLocaleString()}</td>
                    <td style={{ padding: "6px 10px", color: "#EF5350" }}>{r.overspeed_alerts?.toLocaleString()}</td>
                    <td style={{ padding: "6px 10px", color: "#94A3B8" }}>{r.avg_speed} km/h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
