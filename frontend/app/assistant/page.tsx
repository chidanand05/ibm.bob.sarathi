"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 16, marginBottom: 12 } as React.CSSProperties };

const SAMPLE_QUESTIONS = [
  "Which police stations have the highest recorded accident counts?",
  "How have fatal accidents changed over the years?",
  "Which areas contain the most official blackspots?",
  "Which CAS alert type occurs most frequently?",
  "What are the major accident patterns in Bengaluru?",
  "Show accident information for Banaswadi",
];

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function ask(q?: string) {
    const qText = q || question;
    if (!qText.trim()) return;
    setLoading(true);
    setQuestion("");
    try {
      const r = await api.askAssistant(qText);
      setHistory(prev => [...prev, { q: qText, r }]);
    } catch (e: any) {
      setHistory(prev => [...prev, { q: qText, r: { computed_answer: `Error: ${e.message}`, granite_used: false } }]);
    }
    setLoading(false);
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 24, overflowY: "auto", display: "flex", flexDirection: "column" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>AI Assistant</h1>
        <p style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>
          Ask questions about Bengaluru road safety data. Answers are calculated from actual datasets.
          IBM Granite provides enhanced responses when configured.
        </p>

        {/* Sample questions */}
        <div style={C.card}>
          <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Sample questions:</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {SAMPLE_QUESTIONS.map(q => (
              <button key={q} onClick={() => ask(q)}
                style={{ background: "#0D1524", border: "1px solid #1e3050", color: "#94A3B8", borderRadius: 6, padding: "5px 10px", fontSize: 11, cursor: "pointer", textAlign: "left" }}>
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Chat history */}
        <div style={{ flex: 1, marginBottom: 16 }}>
          {history.map((h, i) => (
            <div key={i}>
              <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
                <div style={{ background: "#1a2f50", border: "1px solid #29C8E8", borderRadius: "10px 10px 0 10px", padding: "10px 14px", maxWidth: "70%", fontSize: 13, color: "#e2e8f0" }}>
                  {h.q}
                </div>
              </div>
              <div style={{ display: "flex", marginBottom: 16 }}>
                <div style={{ background: "#0D1524", border: "1px solid #1e3050", borderRadius: "0 10px 10px 10px", padding: "10px 14px", maxWidth: "80%", fontSize: 13 }}>
                  <div style={{ color: "#e2e8f0", lineHeight: 1.6, marginBottom: 8 }}>{h.r.computed_answer}</div>
                  {h.r.granite_response && (
                    <div style={{ marginTop: 8, borderTop: "1px solid #1e3050", paddingTop: 8, color: "#94A3B8", fontSize: 12, lineHeight: 1.5 }}>
                      <span style={{ color: "#29C8E8", fontWeight: 600, fontSize: 11 }}>IBM Granite: </span>{h.r.granite_response}
                    </div>
                  )}
                  {!h.r.granite_used && (
                    <div style={{ fontSize: 10, color: "#475569", marginTop: 4 }}>Deterministic calculation · Configure Granite for LLM responses</div>
                  )}
                  {h.r.stations && (
                    <div style={{ marginTop: 8 }}>
                      {h.r.stations.map((s: any) => (
                        <div key={s.police_station} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 12, borderBottom: "1px solid #0f1a2a" }}>
                          <span style={{ color: "#94A3B8" }}>{s.police_station}</span>
                          <span style={{ color: "#29C8E8" }}>{s.total_accidents} accidents · {s.fatal_accidents} fatal</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {h.r.trends && (
                    <div style={{ marginTop: 8 }}>
                      {h.r.trends.map((t: any) => (
                        <div key={t.year} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 12, borderBottom: "1px solid #0f1a2a" }}>
                          <span style={{ color: "#94A3B8" }}>{t.year}</span>
                          <span style={{ color: "#EF5350" }}>{t.fatal_accidents} fatal</span>
                          <span style={{ color: "#29C8E8" }}>{t.total_accidents} total</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && <div style={{ color: "#29C8E8", fontSize: 13, padding: 10 }}>Calculating from database…</div>}
        </div>

        {/* Input */}
        <div style={{ display: "flex", gap: 10, position: "sticky", bottom: 0, background: "#080D18", paddingTop: 8 }}>
          <input value={question} onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === "Enter" && ask()}
            placeholder="Ask about Bengaluru road safety data…"
            style={{ flex: 1, background: "#0D1524", border: "1px solid #1e3050", color: "#e2e8f0", borderRadius: 8, padding: "10px 14px", fontSize: 13 }} />
          <button onClick={() => ask()} disabled={loading || !question.trim()}
            style={{ background: "#29C8E8", color: "#080D18", border: "none", borderRadius: 8, padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>
            Ask
          </button>
        </div>
      </main>
    </div>
  );
}
