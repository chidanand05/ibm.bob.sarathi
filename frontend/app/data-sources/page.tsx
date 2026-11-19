"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 16, marginBottom: 12 } as React.CSSProperties };

export default function DataSourcesPage() {
  const [sources, setSources] = useState<any[]>([]);
  const [quality, setQuality] = useState<any[]>([]);
  const [reconcile, setReconcile] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      api.dataSources().catch(() => ({ data_sources: [] })),
      api.dataQuality().catch(() => ({ reports: [] })),
      api.reconciliation().catch(() => ({ reconciliation: [] })),
    ]).then(([d, q, r]) => { setSources(d.data_sources || []); setQuality(q.reports || []); setReconcile(r.reconciliation || []); });
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 24, overflowY: "auto" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>Data Sources</h1>
        <p style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>All 6 data sources · Validation status · Known limitations</p>

        {sources.map((s: any) => (
          <div key={s.name} style={C.card}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
              <h3 style={{ color: "#29C8E8", fontSize: 13, fontWeight: 700, margin: 0 }}>{s.name}</h3>
              <span style={{ fontSize: 11, color: s.validation_status === "VALID" ? "#22C55E" : "#EF5350",
                border: `1px solid ${s.validation_status === "VALID" ? "#22C55E" : "#EF5350"}`, borderRadius: 4, padding: "2px 8px" }}>
                {s.validation_status}
              </span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 11 }}>
              {[
                ["Records", s.record_count?.toLocaleString()],
                ["Coverage", s.date_coverage],
                ["Last Processed", s.last_processed?.slice(0, 19)],
                ["Fields", s.available_fields],
              ].map(([k, v]) => (
                <div key={k}><span style={{ color: "#64748b" }}>{k}: </span><span style={{ color: "#94A3B8" }}>{v}</span></div>
              ))}
            </div>
            {s.known_limitations && (
              <div style={{ marginTop: 8, fontSize: 11, color: "#475569", background: "#0a1520", borderRadius: 4, padding: "6px 8px" }}>
                ⚠ {s.known_limitations}
              </div>
            )}
          </div>
        ))}

        {/* Data Reconciliation */}
        {reconcile.length > 0 && (
          <div style={C.card}>
            <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Data Reconciliation Report</h3>
            <p style={{ color: "#64748b", fontSize: 11, marginBottom: 10 }}>
              Minor discrepancies between citywide annual totals and station-level aggregates — documented transparently.
            </p>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead><tr style={{ borderBottom: "1px solid #1e3050" }}>
                {["Year", "Historical Dataset (Fatal)", "Station Aggregate (Fatal)", "Difference", "Status"].map(h =>
                  <th key={h} style={{ padding: "6px 8px", textAlign: "left", color: "#64748b" }}>{h}</th>)}
              </tr></thead>
              <tbody>
                {reconcile.map((r: any) => (
                  <tr key={r.year} style={{ borderBottom: "1px solid #0f1a2a" }}>
                    <td style={{ padding: "5px 8px", color: "#e2e8f0" }}>{r.year}</td>
                    <td style={{ padding: "5px 8px", color: "#94A3B8" }}>{r.historical_dataset_fatal}</td>
                    <td style={{ padding: "5px 8px", color: "#94A3B8" }}>{r.station_level_aggregate_fatal}</td>
                    <td style={{ padding: "5px 8px", color: r.difference !== 0 ? "#F59E0B" : "#22C55E" }}>
                      {r.difference > 0 ? "+" : ""}{r.difference}
                    </td>
                    <td style={{ padding: "5px 8px", color: r.status === "MATCH" ? "#22C55E" : "#F59E0B" }}>{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Quality Reports */}
        <div style={C.card}>
          <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Data Quality Checks</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead><tr style={{ borderBottom: "1px solid #1e3050" }}>
              {["Source", "Check", "Result", "Details"].map(h =>
                <th key={h} style={{ padding: "6px 8px", textAlign: "left", color: "#64748b" }}>{h}</th>)}
            </tr></thead>
            <tbody>
              {quality.slice(0, 30).map((r: any, i: number) => (
                <tr key={i} style={{ borderBottom: "1px solid #0f1a2a" }}>
                  <td style={{ padding: "5px 8px", color: "#29C8E8" }}>{r.source?.split(" ").slice(-2).join(" ")}</td>
                  <td style={{ padding: "5px 8px", color: "#94A3B8" }}>{r.check}</td>
                  <td style={{ padding: "5px 8px", color: r.result === "PASS" ? "#22C55E" : r.result === "FAIL" ? "#EF5350" : "#F59E0B" }}>{r.result}</td>
                  <td style={{ padding: "5px 8px", color: "#64748b", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
