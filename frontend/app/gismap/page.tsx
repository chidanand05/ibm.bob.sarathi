"use client";
import { useEffect, useRef, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

const C = { card: { background: "#111C2D", border: "1px solid #1e3050", borderRadius: 10, padding: 16, marginBottom: 12 } as React.CSSProperties };
const sel = { background: "#0D1524", border: "1px solid #1e3050", color: "#e2e8f0", borderRadius: 6, padding: "6px 10px", fontSize: 12 } as React.CSSProperties;

const RISK_COLORS: Record<string, string> = {
  HIGH: "#EF5350", MEDIUM_HIGH: "#F59E0B", MODERATE: "#EAB308", LOW: "#22C55E"
};

function getRiskColor(tier: string) { return RISK_COLORS[tier] || "#475569"; }

export default function GISMapPage() {
  const mapRef = useRef<any>(null);
  const mapInstanceRef = useRef<any>(null);
  const [stations, setStations] = useState<any[]>([]);
  const [blackspots, setBlackspots] = useState<any[]>([]);
  const [casPoints, setCasPoints] = useState<any[]>([]);
  const [layers, setLayers] = useState({ accidents: true, blackspots: true, cas: true });
  const [year, setYear] = useState(2024);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const leafletLayersRef = useRef<any>({});

  useEffect(() => {
    Promise.all([
      api.mapStations(year).catch(() => ({ stations: [] })),
      api.mapBlackspots().catch(() => ({ blackspots: [] })),
      api.mapCasAlerts().catch(() => ({ heatmap_points: [] })),
    ]).then(([s, b, c]) => {
      setStations(s.stations || []);
      setBlackspots(b.blackspots || []);
      setCasPoints(c.heatmap_points || []);
      setLoading(false);
    });
  }, [year]);

  useEffect(() => {
    if (loading || typeof window === "undefined") return;
    if (!mapInstanceRef.current) {
      initMap();
    } else {
      refreshLayers();
    }
  }, [loading, stations, blackspots, casPoints, layers]);

  function initMap() {
    const L = (window as any).L;
    if (!L || !mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, { center: [12.9716, 77.5946], zoom: 11 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18
    }).addTo(map);
    mapInstanceRef.current = map;
    refreshLayers();
  }

  function refreshLayers() {
    const L = (window as any).L;
    const map = mapInstanceRef.current;
    if (!L || !map) return;

    // Clear old layers
    Object.values(leafletLayersRef.current).forEach((lg: any) => map.removeLayer(lg));
    leafletLayersRef.current = {};

    // Accident station circles
    if (layers.accidents) {
      const lg = L.layerGroup();
      stations.forEach((s: any) => {
        const color = getRiskColor(s.risk_tier);
        const radius = Math.max(300, Math.min(1500, s.total_accidents * 15));
        const circle = L.circle([s.lat, s.lng], {
          color, fillColor: color, fillOpacity: 0.5, radius, weight: 2
        }).bindPopup(`
          <div style="font-family:sans-serif;min-width:200px">
            <b style="color:#1e3a5f;font-size:14px">${s.police_station}</b><br/>
            <span style="color:#666;font-size:11px">Zone: ${s.zone} · Risk: <b style="color:${color}">${s.risk_tier}</b></span>
            <hr style="border:none;border-top:1px solid #eee;margin:6px 0"/>
            <table style="font-size:12px;width:100%">
              <tr><td>Total Accidents</td><td><b>${s.total_accidents}</b></td></tr>
              <tr><td>Fatal</td><td style="color:#c0392b"><b>${s.fatal_accidents}</b></td></tr>
              <tr><td>Non-Fatal</td><td>${s.non_fatal_accidents}</td></tr>
              <tr><td>People Killed</td><td style="color:#c0392b">${s.people_killed}</td></tr>
              <tr><td>Risk Score</td><td><b>${s.risk_score}/100</b></td></tr>
              <tr><td>YoY Change</td><td style="color:${s.yoy_change_pct > 0 ? '#c0392b' : '#27ae60'}">${s.yoy_change_pct > 0 ? '+' : ''}${s.yoy_change_pct}%</td></tr>
              <tr><td>Blackspots</td><td>${s.blackspot_count}</td></tr>
            </table>
            <div style="font-size:10px;color:#999;margin-top:6px">Year: ${s.year} · Source: BTP accident data</div>
          </div>
        `).on("click", () => setSelected(s));
        lg.addLayer(circle);
      });
      leafletLayersRef.current.accidents = lg;
      lg.addTo(map);
    }

    // Official BTP Blackspot markers
    if (layers.blackspots) {
      const lg = L.layerGroup();
      blackspots.forEach((bs: any) => {
        const icon = L.divIcon({
          html: `<div style="background:#EF5350;width:12px;height:12px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,0.5)"></div>`,
          className: "", iconAnchor: [6, 6]
        });
        L.marker([bs.lat, bs.lng], { icon }).bindPopup(`
          <div style="font-family:sans-serif;min-width:200px">
            <b style="color:#c0392b;font-size:12px">🔴 Official BTP Blackspot</b><br/>
            <b style="font-size:13px">${bs.normalized_location_name}</b><br/>
            <div style="font-size:11px;color:#555;margin-top:4px">${bs.original_location_description}</div>
            <hr style="border:none;border-top:1px solid #eee;margin:6px 0"/>
            <div style="font-size:11px"><b>Station:</b> ${bs.police_station}</div>
            <div style="font-size:11px"><b>Road:</b> ${bs.road_name}</div>
            <div style="font-size:11px"><b>Type:</b> ${bs.location_type}</div>
            <div style="font-size:11px"><b>ID:</b> ${bs.blackspot_id}</div>
            ${bs.identification_year ? `<div style="font-size:11px"><b>Year:</b> ${bs.identification_year}</div>` : ''}
            <div style="font-size:10px;color:#999;margin-top:4px">Source: ${bs.source} · ${bs.geocoding_status}</div>
          </div>
        `).addTo(lg);
      });
      leafletLayersRef.current.blackspots = lg;
      lg.addTo(map);
    }

    // CAS Alert Heatmap dots
    if (layers.cas && casPoints.length) {
      const lg = L.layerGroup();
      casPoints.slice(0, 500).forEach((p: any) => {
        const opacity = Math.min(0.8, p.intensity / 2000);
        const r = Math.max(2, Math.min(14, p.intensity / 300));
        L.circleMarker([p.lat, p.lng], {
          radius: r, color: "#F59E0B", fillColor: "#F59E0B",
          fillOpacity: opacity, weight: 0
        }).bindPopup(`
          <div style="font-family:sans-serif;font-size:12px">
            <b>CAS Alert Cluster</b><br/>
            Total alerts: <b>${p.intensity}</b><br/>
            Overspeed alerts: ${p.overspeed || 0}<br/>
            <i style="color:#999;font-size:10px">Driving-safety alerts, not accidents</i>
          </div>
        `).addTo(lg);
      });
      leafletLayersRef.current.cas = lg;
      lg.addTo(map);
    }
  }

  // Load Leaflet CSS + JS on client
  useEffect(() => {
    if (typeof window === "undefined") return;
    if ((window as any).L) { if (!loading) initMap(); return; }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(link);
    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = () => { if (!loading) initMap(); };
    document.head.appendChild(script);
  }, [loading]);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080D18" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 20, overflowY: "auto" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: "#e2e8f0", marginBottom: 4 }}>Bengaluru GIS Map</h1>
        <p style={{ color: "#64748b", fontSize: 12, marginBottom: 16 }}>Interactive accident risk choropleth · Official BTP blackspots · CAS alert heatmap</p>

        <div style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
          <select style={sel} value={year} onChange={e => { setYear(+e.target.value); setLoading(true); }}>
            {[2024, 2023, 2022, 2021, 2020, 2019, 2018].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
          <label style={{ color: "#94A3B8", fontSize: 12, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={layers.accidents} onChange={e => setLayers(l => ({ ...l, accidents: e.target.checked }))} />
            <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#29C8E8", display: "inline-block" }} />
            Accident Risk (station circles)
          </label>
          <label style={{ color: "#94A3B8", fontSize: 12, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={layers.blackspots} onChange={e => setLayers(l => ({ ...l, blackspots: e.target.checked }))} />
            <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#EF5350", display: "inline-block" }} />
            Official BTP Blackspots (64)
          </label>
          <label style={{ color: "#94A3B8", fontSize: 12, display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={layers.cas} onChange={e => setLayers(l => ({ ...l, cas: e.target.checked }))} />
            <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#F59E0B", display: "inline-block" }} />
            CAS Alert Clusters (Feb–Jul 2018)
          </label>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16 }}>
          {/* Map */}
          <div style={{ ...C.card, padding: 0, overflow: "hidden" }}>
            <div ref={mapRef} style={{ height: 520, width: "100%", background: "#0D1524" }}>
              {loading && <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#29C8E8", fontSize: 14 }}>Loading map data…</div>}
            </div>
          </div>

          {/* Legend + Selected info */}
          <div>
            <div style={C.card}>
              <h3 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Risk Legend</h3>
              {Object.entries(RISK_COLORS).map(([tier, color]) => (
                <div key={tier} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span style={{ width: 14, height: 14, borderRadius: "50%", background: color, display: "inline-block", flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: "#94A3B8" }}>{tier.replace("_", " ")}</span>
                </div>
              ))}
              <div style={{ marginTop: 8, borderTop: "1px solid #1e3050", paddingTop: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#EF5350", display: "inline-block" }} />
                  <span style={{ fontSize: 11, color: "#94A3B8" }}>Official BTP Blackspot</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#F59E0B", display: "inline-block" }} />
                  <span style={{ fontSize: 11, color: "#94A3B8" }}>CAS Alert Cluster</span>
                </div>
              </div>
              <div style={{ marginTop: 8, fontSize: 10, color: "#475569", borderTop: "1px solid #1e3050", paddingTop: 8 }}>
                Circle size = accident count. Click any marker for details.
              </div>
            </div>

            {/* Stats */}
            <div style={C.card}>
              <h3 style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 600, marginBottom: 8 }}>Layer Statistics</h3>
              <div style={{ fontSize: 12, color: "#94A3B8" }}>
                <div>Stations: <b style={{ color: "#29C8E8" }}>{stations.length}</b></div>
                <div>Blackspots: <b style={{ color: "#EF5350" }}>{blackspots.length}</b></div>
                <div>CAS clusters: <b style={{ color: "#F59E0B" }}>{casPoints.length}</b></div>
                <div style={{ marginTop: 6, fontSize: 10, color: "#475569" }}>Showing {year} accident data</div>
              </div>
            </div>

            {/* Selected station info */}
            {selected && (
              <div style={{ ...C.card, borderColor: "#29C8E8" }}>
                <h3 style={{ color: "#29C8E8", fontSize: 12, fontWeight: 700, marginBottom: 8 }}>{selected.police_station}</h3>
                <div style={{ fontSize: 11 }}>
                  {[
                    ["Zone", selected.zone], ["Risk", selected.risk_tier], ["Score", `${selected.risk_score}/100`],
                    ["Total", selected.total_accidents], ["Fatal", selected.fatal_accidents],
                    ["Killed", selected.people_killed], ["YoY", `${selected.yoy_change_pct > 0 ? "+" : ""}${selected.yoy_change_pct}%`],
                    ["Blackspots", selected.blackspot_count]
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
                      <span style={{ color: "#64748b" }}>{k}</span>
                      <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ ...C.card, background: "#0a1520", borderColor: "#F59E0B", borderLeftWidth: 4, fontSize: 11, color: "#94A3B8" }}>
          <strong style={{ color: "#F59E0B" }}>Map Note:</strong> Station circles use accident frequency data from BTP datasets.
          Station boundaries are approximated by central coordinates. Exact police jurisdiction boundaries require a verified GeoJSON dataset.
          BTP blackspot coordinates are derived from official location descriptions and require field verification.
          CAS alerts are driving-safety indicators (Feb–Jul 2018), not confirmed accident records.
        </div>
      </main>
    </div>
  );
}
