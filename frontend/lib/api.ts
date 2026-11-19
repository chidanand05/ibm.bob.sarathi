const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  health: () => apiFetch("/api/health"),
  summary: () => apiFetch("/api/dashboard/summary"),
  annualTrends: () => apiFetch("/api/accidents/annual"),
  byStation: (year?: number, zone?: string) =>
    apiFetch(`/api/accidents/by-station?${year ? `year=${year}&` : ""}${zone ? `zone=${zone}` : ""}`),
  trends: (station?: string) =>
    apiFetch(`/api/accidents/trends${station ? `?police_station=${encodeURIComponent(station)}` : ""}`),
  blackspots: (station?: string) =>
    apiFetch(`/api/blackspots${station ? `?police_station=${encodeURIComponent(station)}` : ""}`),
  blackspotDetail: (id: string) => apiFetch(`/api/blackspots/${id}`),
  mapStations: (year?: number) => apiFetch(`/api/map/police-stations${year ? `?year=${year}` : ""}`),
  mapBlackspots: () => apiFetch("/api/map/blackspots"),
  mapCasAlerts: () => apiFetch("/api/map/cas-alerts"),
  casSummary: () => apiFetch("/api/cas/summary"),
  casByWard: () => apiFetch("/api/cas/by-ward?limit=50"),
  casByAlarmType: () => apiFetch("/api/cas/by-alarm-type"),
  casOverspeed: () => apiFetch("/api/cas/overspeeding"),
  riskStations: () => apiFetch("/api/risk/stations"),
  recommendations: (station?: string) =>
    apiFetch(`/api/recommendations${station ? `?police_station=${encodeURIComponent(station)}` : ""}`),
  agents: () => apiFetch("/api/agents"),
  runAgent: (body: object) => apiFetch("/api/agents/analyze", { method: "POST", body: JSON.stringify(body) }),
  askAssistant: (question: string) =>
    apiFetch("/api/assistant/query", { method: "POST", body: JSON.stringify({ question }) }),
  dataSources: () => apiFetch("/api/data-sources"),
  dataQuality: () => apiFetch("/api/data-quality"),
  reconciliation: () => apiFetch("/api/accidents/reconciliation"),
  agentLogs: () => apiFetch("/api/agent-logs"),
};
