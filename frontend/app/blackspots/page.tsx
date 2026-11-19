"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 16, marginBottom: 12 } as React.CSSProperties };

export default function BlackspotsPage() {
  const [bsList, setBsList] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [stationFilter, setStationFilter] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.blackspots().then(r => { setBsList(r.blackspots || []); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const stations = Array.from(new Set(bsList.map((b: any) => b.police_station))).sort();
  const filtered = bsList.filter((b: any) =>
    (!stationFilter || b.police_station === stationFilter) &&
    (!search || b.normalized_location_name.toLowerCase().includes(search.toLowerCase()) ||
     b.original_location_description.toLowerCase().includes(search.toLowerCase()) ||
     b.road_name.toLowerCase().includes(search.toLowerCase()))
  );

  const grouped = filtered.reduce((acc: any, b: any) => {
    if (!acc[b.police_station]) acc[b.police_station] = [];
    acc[b.police_station].push(b);
    return acc;
  }, {});

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 24, overflowY: "auto" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>Blackspot Intelligence</h1>
        <p style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>
          64 Official Bengaluru Traffic Police Blackspot Locations · Source: BTP
        </p>

        <div style={{ background: "#0a1520", border: "1px solid #EF5350", borderLeftWidth: 4, borderRadius: 6, padding: "10px 14px", marginBottom: 16, fontSize: 11, color: "#94A3B8" }}>
          <b style={{ color: "#EF5350" }}>IMPORTANT:</b> Official BTP Blackspots are locations officially designated by Bengaluru Traffic Police.
          Data-derived high-accident station rankings are shown separately and must NOT be confused with officially designated blackspots.
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          <input placeholder="Search location, road name…" value={search} onChange={e => setSearch(e.target.value)}
            style={{ background: "#0D1524", border: "1px solid #1e3050", color: "#e2e8f0", borderRadius: 6, padding: "7px 12px", fontSize: 12, minWidth: 240 }} />
          <select value={stationFilter} onChange={e => setStationFilter(e.target.value)}
            style={{ background: "#0D1524", border: "1px solid #1e3050", color: "#e2e8f0", borderRadius: 6, padding: "7px 10px", fontSize: 12 }}>
            <option value="">All Police Stations</option>
            {stations.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <span style={{ color: "#64748b", fontSize: 12, padding: "7px 0" }}>Showing {filtered.length} of {bsList.length} blackspots</span>
        </div>

        {loading ? <div style={{ color: "#29C8E8" }}>Loading…</div> : (
          <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 350px" : "1fr", gap: 16 }}>
            <div>
              {Object.keys(grouped).sort().map(station => (
                <div key={station} style={C.card}>
                  <h3 style={{ color: "#29C8E8", fontSize: 13, fontWeight: 700, marginBottom: 10 }}>
                    📍 {station} <span style={{ color: "#64748b", fontWeight: 400 }}>({grouped[station].length} blackspot{grouped[station].length > 1 ? "s" : ""})</span>
                  </h3>
                  {grouped[station].map((bs: any) => (
                    <div key={bs.blackspot_id} onClick={() => setSelected(bs)}
                      style={{ padding: "8px 10px", cursor: "pointer", borderRadius: 6, marginBottom: 4,
                        background: selected?.blackspot_id === bs.blackspot_id ? "#1a2f50" : "#0D1524",
                        border: `1px solid ${selected?.blackspot_id === bs.blackspot_id ? "#29C8E8" : "#1e3050"}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ fontSize: 12, color: "#e2e8f0" }}>{bs.normalized_location_name}</span>
                        <span style={{ fontSize: 11, color: "#64748b" }}>{bs.blackspot_id}</span>
                      </div>
                      <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 2 }}>{bs.road_name} · {bs.location_type}</div>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {selected && (
              <div style={{ position: "sticky", top: 0 }}>
                <div style={{ ...C.card, borderColor: "#EF5350" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ fontSize: 11, color: "#EF5350", fontWeight: 700 }}>🔴 OFFICIAL BTP BLACKSPOT</span>
                    <span style={{ fontSize: 11, color: "#64748b", cursor: "pointer" }} onClick={() => setSelected(null)}>✕</span>
                  </div>
                  <h3 style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 700, marginBottom: 10 }}>{selected.normalized_location_name}</h3>
                  <div style={{ fontSize: 11, color: "#94A3B8", marginBottom: 10, fontStyle: "italic", lineHeight: 1.5, background: "#0a1520", padding: "8px 10px", borderRadius: 6 }}>
                    "{selected.original_location_description}"
                  </div>
                  {[
                    ["Blackspot ID", selected.blackspot_id],
                    ["Police Station", selected.police_station],
                    ["Road Name", selected.road_name],
                    ["Location Type", selected.location_type],
                    ["Source", selected.source],
                    ["Identified", selected.identification_year || "Not specified"],
                    ["Latitude", selected.latitude?.toFixed(6)],
                    ["Longitude", selected.longitude?.toFixed(6)],
                    ["Geocoding", selected.geocoding_status],
                    ["Verification", selected.verification_status],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #0f1a2a", fontSize: 12 }}>
                      <span style={{ color: "#64748b" }}>{k}</span>
                      <span style={{ color: "#e2e8f0", textAlign: "right", maxWidth: 160, wordBreak: "break-all" }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
