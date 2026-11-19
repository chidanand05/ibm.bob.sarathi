"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 20, marginBottom: 16 } as React.CSSProperties };
const sel = { background: "#0D1524", border: "1px solid #1e3050", color: "#e2e8f0", borderRadius: 6, padding: "6px 10px", fontSize: 13 } as React.CSSProperties;

const ZONES = ["", "East", "North", "South", "Central", "West"];
const YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018];

export default function AnalyticsPage() {
  const [year, setYear] = useState(2024);
  const [zone, setZone] = useState("");
  const [station, setStation] = useState("");
  const [stationData, setStationData] = useState<any[]>([]);
  const [trends, setTrends] = useState<any[]>([]);
  const [stationTrend, setStationTrend] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.byStation(year, zone || undefined).catch(() => ({ data: [] })),
      api.annualTrends().catch(() => ({ data: [] })),
    ]).then(([s, t]) => {
      setStationData(s.data || []);
      setTrends(t.data || []);
      setLoading(false);
    });
  }, [year, zone]);

  useEffect(() => {
    if (!station) { setStationTrend(null); return; }
    api.trends(station).then(setStationTrend).catch(() => null);
  }, [station]);

  const fatalPct = stationData.length ? Math.round(stationData.reduce((a, r) => a + (r.fatal_accidents || 0), 0) / Math.max(1, stationData.reduce((a, r) => a + (r.total_accidents || 0), 0)) * 100) : 0;

  return (
    <Layout>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>Accident Analytics</h1>
      <p style={{ color: "#64748b", fontSize: 13, marginBottom: 20 }}>Station-level accident statistics · Source: BTP datasets 2018–2024</p>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <select style={sel} value={year} onChange={e => setYear(+e.target.value)}>
          {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <select style={sel} value={zone} onChange={e => setZone(e.target.value)}>
          {ZONES.map(z => <option key={z} value={z}>{z || "All Zones"}</option>)}
        </select>
        <select style={sel} value={station} onChange={e => setStation(e.target.value)}>
          <option value="">Select Station (Trend)</option>
          {stationData.map((r: any) => <option key={r.police_station} value={r.police_station}>{r.police_station}</option>)}
        </select>
      </div>

      {loading ? <div style={{ color: "#29C8E8" }}>Loading…</div> : (
        <>
          {/* Summary row */}
          <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
            {[
              { label: "Stations", val: stationData.length, c: "#29C8E8" },
              { label: `Total Accidents ${year}`, val: stationData.reduce((a, r) => a + (r.total_accidents || 0), 0).toLocaleString(), c: "#29C8E8" },
              { label: "Fatal", val: stationData.reduce((a, r) => a + (r.fatal_accidents || 0), 0), c: "#EF5350" },
              { label: "Non-Fatal", val: stationData.reduce((a, r) => a + (r.non_fatal_accidents || 0), 0), c: "#F59E0B" },
              { label: "Fatality Rate", val: `${fatalPct}%`, c: "#EF5350" },
            ].map(k => (
              <div key={k.label} style={{ ...C.card, flex: 1, minWidth: 120, textAlign: "center", marginBottom: 0 }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: k.c }}>{k.val}</div>
                <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 4 }}>{k.label}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* Fatal vs Non-Fatal Bar */}
            <div style={C.card}>
              <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Fatal vs Non-Fatal by Station ({year})</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={stationData.slice(0, 15)} margin={{ left: 10, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3050" />
                  <XAxis dataKey="police_station" stroke="#64748b" tick={{ fontSize: 9, angle: -35, textAnchor: "end" }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="fatal_accidents" fill="#EF5350" name="Fatal" stackId="a" />
                  <Bar dataKey="non_fatal_accidents" fill="#29C8E8" name="Non-Fatal" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Citywide Annual Trend */}
            <div style={C.card}>
              <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Citywide Annual Trend (2007–2025)</h3>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3050" />
                  <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="total_accidents" stroke="#29C8E8" dot={false} name="Total" strokeWidth={2} />
                  <Line type="monotone" dataKey="fatal_accidents" stroke="#EF5350" dot={false} name="Fatal" strokeWidth={2} />
                  <Line type="monotone" dataKey="people_killed" stroke="#F59E0B" dot={false} name="Killed" strokeWidth={1} strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Station Trend */}
          {stationTrend && stationTrend.years && (
            <div style={C.card}>
              <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>
                Historical Trend: {stationTrend.police_station}
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={stationTrend.years.map((y: number, i: number) => ({
                  year: y, total: stationTrend.total_accidents[i], fatal: stationTrend.fatal_accidents[i],
                  killed: stationTrend.people_killed[i]
                }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e3050" />
                  <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#0D1524", border: "1px solid #1e3050", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="total" stroke="#29C8E8" dot name="Total" strokeWidth={2} />
                  <Line type="monotone" dataKey="fatal" stroke="#EF5350" dot name="Fatal" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Station Table */}
          <div style={C.card}>
            <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Station Rankings ({year})</h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #1e3050" }}>
                    {["#", "Station", "Zone", "Total", "Fatal", "Non-Fatal", "Killed", "Injured"].map(h => (
                      <th key={h} style={{ padding: "8px 10px", textAlign: "left", color: "#64748b", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {stationData.map((r: any, i: number) => (
                    <tr key={r.police_station} style={{ borderBottom: "1px solid #0f1a2a" }}
                        onClick={() => setStation(r.police_station)} style2={{ cursor: "pointer" }}>
                      <td style={{ padding: "7px 10px", color: "#64748b" }}>{i + 1}</td>
                      <td style={{ padding: "7px 10px", color: "#29C8E8", cursor: "pointer" }}
                          onClick={() => setStation(r.police_station)}>{r.police_station}</td>
                      <td style={{ padding: "7px 10px", color: "#94A3B8" }}>{r.zone}</td>
                      <td style={{ padding: "7px 10px", color: "#e2e8f0", fontWeight: 600 }}>{r.total_accidents}</td>
                      <td style={{ padding: "7px 10px", color: "#EF5350" }}>{r.fatal_accidents}</td>
                      <td style={{ padding: "7px 10px", color: "#F59E0B" }}>{r.non_fatal_accidents}</td>
                      <td style={{ padding: "7px 10px", color: "#EF5350" }}>{r.people_killed}</td>
                      <td style={{ padding: "7px 10px", color: "#94A3B8" }}>{r.people_injured}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}><Sidebar /><main style={{ flex: 1, padding: 24, overflowY: "auto" }}>{children}</main></div>;
}
