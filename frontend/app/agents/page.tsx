"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 16, marginBottom: 12 } as React.CSSProperties };
const STATUS_COLOR: Record<string, string> = { active: "#22C55E", awaiting_data: "#F59E0B", failed: "#EF5350" };

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [granite, setGranite] = useState<any>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});
  const [logs, setLogs] = useState<any[]>([]);
  const [station, setStation] = useState("");

  useEffect(() => {
    api.agents().then(r => { setAgents(r.agents || []); setGranite(r.granite_status); });
    api.agentLogs().then(r => setLogs((r.logs || []).slice(0, 20)));
  }, []);

  async function runAgent(agentId: string) {
    setRunning(agentId);
    try {
      const r = await api.runAgent({ agent_id: agentId, police_station: station || undefined });
      setResults(prev => ({ ...prev, [agentId]: r }));
      api.agentLogs().then(r => setLogs((r.logs || []).slice(0, 20)));
    } catch (e: any) {
      setResults(prev => ({ ...prev, [agentId]: { error: e.message } }));
    }
    setRunning(null);
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 24, overflowY: "auto" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>AI Agents</h1>
        <p style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>Five specialized road safety agents with distinct computational responsibilities</p>

        {/* IBM Granite status */}
        {granite && (
          <div style={{ ...C.card, borderColor: granite.available ? "#22C55E" : "#F59E0B" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: granite.available ? "#22C55E" : "#F59E0B", display: "inline-block" }} />
              <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>IBM Granite / watsonx.ai</span>
              <span style={{ fontSize: 11, color: granite.available ? "#22C55E" : "#F59E0B" }}>
                {granite.available ? `Connected · ${granite.model}` : "Fallback active — configure WATSONX_API_KEY in backend/.env"}
              </span>
            </div>
          </div>
        )}

        {/* Station filter */}
        <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
          <input placeholder="Optional: Filter by police station…" value={station} onChange={e => setStation(e.target.value)}
            style={{ background: "#0D1524", border: "1px solid #1e3050", color: "#e2e8f0", borderRadius: 6, padding: "7px 12px", fontSize: 12, minWidth: 280 }} />
          <button onClick={() => runAgent("all")} disabled={running !== null}
            style={{ background: "#29C8E8", color: "#080D18", border: "none", borderRadius: 6, padding: "7px 16px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
            {running === "all" ? "Running…" : "▶ Run Full Analysis"}
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {agents.map((ag: any) => (
            <div key={ag.id} style={{ ...C.card, borderColor: results[ag.id] ? "#29C8E8" : "#1e3050" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div>
                  <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: STATUS_COLOR[ag.status] || "#64748b", marginRight: 6 }} />
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0" }}>{ag.name}</span>
                </div>
                <button onClick={() => runAgent(ag.id)} disabled={running !== null}
                  style={{ background: running === ag.id ? "#1e3050" : "#0D1524", border: "1px solid #1e3050", color: "#29C8E8", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: "pointer" }}>
                  {running === ag.id ? "Running…" : "Run"}
                </button>
              </div>
              <p style={{ fontSize: 11, color: "#94A3B8", marginBottom: 8, lineHeight: 1.5 }}>{ag.description}</p>
              <div style={{ fontSize: 11 }}>
                <div style={{ color: "#64748b" }}>Algorithm: <span style={{ color: "#94A3B8" }}>{ag.algorithm}</span></div>
                <div style={{ color: "#64748b", marginTop: 2 }}>Inputs: <span style={{ color: "#94A3B8" }}>{ag.inputs?.join(", ")}</span></div>
              </div>
              {results[ag.id] && (
                <div style={{ marginTop: 8, background: "#0D1524", borderRadius: 6, padding: 8 }}>
                  <div style={{ fontSize: 10, color: "#22C55E", fontWeight: 700, marginBottom: 4 }}>✓ COMPLETED</div>
                  <pre style={{ fontSize: 10, color: "#94A3B8", overflow: "auto", maxHeight: 120, whiteSpace: "pre-wrap", margin: 0 }}>
                    {JSON.stringify(results[ag.id], null, 2).slice(0, 800)}…
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Execution Logs */}
        <div style={{ ...C.card, marginTop: 16 }}>
          <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Execution Log</h3>
          {logs.length === 0 ? <div style={{ color: "#64748b", fontSize: 12 }}>No execution logs yet. Run an agent above.</div> : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead><tr style={{ borderBottom: "1px solid #1e3050" }}>
                {["Agent", "Task", "Status", "Time (ms)", "Timestamp"].map(h =>
                  <th key={h} style={{ padding: "6px 8px", textAlign: "left", color: "#64748b" }}>{h}</th>)}
              </tr></thead>
              <tbody>
                {logs.map((l: any, i: number) => (
                  <tr key={i} style={{ borderBottom: "1px solid #0f1a2a" }}>
                    <td style={{ padding: "5px 8px", color: "#29C8E8" }}>{l.agent?.replace(" Agent", "")}</td>
                    <td style={{ padding: "5px 8px", color: "#94A3B8", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.task}</td>
                    <td style={{ padding: "5px 8px", color: l.status === "completed" ? "#22C55E" : l.status === "failed" ? "#EF5350" : "#F59E0B" }}>{l.status}</td>
                    <td style={{ padding: "5px 8px", color: "#94A3B8" }}>{l.execution_ms}</td>
                    <td style={{ padding: "5px 8px", color: "#64748b" }}>{l.timestamp?.slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
