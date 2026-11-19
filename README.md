# ParallaX — Bengaluru Road Safety & Accident Risk Intelligence Platform

**IBM Inter-Institute Hackathon | Problem Statement 8 | Team ParallaX**

> *AI-Powered Urban Accident Analytics & Blackspot Intelligence*  
> Five specialized AI agents · 207,575 CAS records · 64 Official BTP blackspots · Interactive GIS map

---

## 1. Project Introduction

ParallaX is a full-stack, data-driven road safety intelligence platform for Bengaluru, India. It ingests six real datasets — five years of accident statistics and one geographical driving-safety alert dataset — and uses five specialized AI agents to analyze risk, identify blackspots, assess road conditions, generate evidence-based safety recommendations, and present everything through an interactive GIS-powered analytics dashboard.

**Key facts:**
- Bengaluru recorded **4,769 accidents, 869 fatal** in 2024
- **64 official Bengaluru Traffic Police blackspot locations** mapped and analyzed
- **207,575 CAS driving-safety alert records** spatially aggregated for heatmap visualization
- Risk scoring across **34 police stations** using transparent normalized methodology

---

## 2. Architecture

```
ParallaX_Road_Safety_Intelligence_Platform/
├── backend/                  # Python FastAPI backend
│   ├── main.py               # 25+ REST API endpoints
│   ├── agents/               # Five specialized AI agents
│   │   ├── accident_risk_agent.py     # Agent 1 — Risk prediction
│   │   ├── blackspot_agent.py         # Agent 2 — Blackspot analysis
│   │   ├── road_condition_agent.py    # Agent 3 — Road conditions
│   │   ├── recommendation_agent.py    # Agent 4 — Safety recommendations
│   │   ├── dashboard_agent.py         # Agent 5 — Analytics + Q&A
│   │   └── orchestrator.py            # Agent coordinator
│   ├── database/
│   │   ├── db.py             # SQLite connection + session management
│   │   ├── models.py         # 10 ORM tables
│   │   └── ingestion.py      # Automated data pipeline for all 6 CSVs
│   ├── services/
│   │   └── granite_client.py # IBM Granite / watsonx.ai integration
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Next.js 15 TypeScript frontend
│   ├── app/
│   │   ├── overview/         # KPI cards + trend charts
│   │   ├── analytics/        # Station-level accident analytics + filters
│   │   ├── gismap/           # Interactive Leaflet choropleth map (3 layers)
│   │   ├── blackspots/       # 64 Official BTP blackspot browser
│   │   ├── cas/              # CAS alert analysis + charts
│   │   ├── agents/           # AI agent execution interface + logs
│   │   ├── recommendations/  # Evidence-based safety recommendations
│   │   ├── data-sources/     # Data quality + reconciliation reports
│   │   └── assistant/        # AI Q&A interface (IBM Granite / fallback)
│   ├── components/Sidebar.tsx
│   ├── lib/api.ts            # Backend API client
│   ├── package.json
│   └── postcss.config.mjs
├── data/raw/                 # All 6 CSV data sources (included)
├── scripts/                  # Utility scripts directory
├── start.sh                  # One-command startup script
└── README.md
```

---

## 3. Features and Five AI Agents

### Dashboard Features
- **KPI Overview**: Total accidents, fatal accidents, people killed/injured, official blackspots, CAS alerts
- **Annual Trends (2007–2025)**: 19-year citywide trend chart
- **Station Rankings**: Top stations by accident count and fatality rate
- **Zone Analysis**: East / North / South / Central / West breakdowns
- **Interactive GIS Map**: Accident choropleth + official blackspot markers + CAS alert heatmap
- **AI Assistant**: Natural-language Q&A powered by IBM Granite (or deterministic fallback)

### Five AI Agents

| # | Agent | Algorithm | Status |
|---|-------|-----------|--------|
| 1 | **Accident Risk Prediction** | Normalized severity-weighted scoring (60% fatal + 40% total) + SHAP-style factor attribution + pedestrian context from blackspot types | ✅ Active |
| 2 | **Blackspot Identification** | Official BTP registry (64 locations) + data-derived frequency ranking. Two distinct categories maintained; never conflated | ✅ Active |
| 3 | **Road Condition Analysis** | CAS overspeed alert proxy; YOLOv8 integration interface ready for image data | ⚠️ Awaiting image data |
| 4 | **Road Safety Recommendations** | Intervention knowledge base + evidence-strength ranking (STRONG / MODERATE / INDICATIVE) | ✅ Active (58 recommendations) |
| 5 | **Analytics Dashboard** | Data aggregation + IBM Granite LLM Q&A with deterministic fallback | ✅ Active |

---

## 4. Datasets

| File | Description | Records | Coverage |
|------|-------------|---------|----------|
| `accident_stats_2024.csv` | Zone/subdivision/station breakdown 2024 | 58 rows | 2024 |
| `accident_stats_2021_2022.csv` | Station-level fatal/non-fatal/injured | 33 stations × 2 yrs | 2021–2022 |
| `historical_annual_accident_stats.csv` | Citywide annual totals | 19 rows | 2007–2025 |
| `accident_stats_2023.csv` | Station-level 2023 | 39 rows | 2023 |
| `accident_stats_2018_2020.csv` | Station-level multi-year | 33 stations × 3 yrs | 2018–2020 |
| `bangalore-cas-alerts.csv` | CAS driving-safety alerts | **207,617 raw → 207,575 valid** | Feb–Jul 2018 |
| `bengaluru_traffic_police_blackspots.csv` | Official BTP blackspots | **64 locations** | Official |

> **Important**: CAS alerts are driving-safety indicators (Collision Avoidance System), not confirmed accidents.

---

## 5. Software Prerequisites

Install these before setup:

- **Python 3.12** — https://www.python.org/downloads/
- **Node.js 20+** — https://nodejs.org/
- **npm 10+** — bundled with Node.js
- **Git** (optional, for cloning)

Verify versions:
```bash
python3 --version    # Should show 3.12.x
node --version       # Should show 20.x or higher
npm --version        # Should show 10.x or higher
```

---

## 6. Python Environment Setup (Python 3.12)

```bash
# Navigate to the project root
cd ParallaX_Road_Safety_Intelligence_Platform

# Create virtual environment with Python 3.12
python3.12 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Confirm Python version
python --version    # Should show Python 3.12.x
```

---

## 7. Backend Dependency Installation

```bash
# With venv active
pip install --upgrade pip
pip install -r backend/requirements.txt
```

**Key packages installed:**
- `fastapi` — REST API framework
- `uvicorn` — ASGI server
- `sqlalchemy` — ORM + SQLite
- `pandas` + `numpy` — data processing
- `scikit-learn` — ML utilities
- `requests` + `httpx` — HTTP clients
- `python-dotenv` — environment config

---

## 8. Frontend Dependency Installation

```bash
cd frontend
npm install --legacy-peer-deps
cd ..
```

**Key packages:** Next.js 15, React 19, TypeScript, Tailwind CSS v4, Recharts, Leaflet, Lucide React

---

## 9. Environment Variable Configuration

### Backend (optional — for IBM Granite)
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```
WATSONX_API_KEY=your_watsonx_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

> **Without these credentials, the application runs fully in deterministic fallback mode** — all 5 agents, all APIs, and all dashboard features work without IBM Granite.

### Frontend
The file `frontend/.env.local` is already configured:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
No changes needed for local development.

---

## 10. Database Initialization and Data Ingestion

The SQLite database (`backend/road_safety.db`) is **not included** in this package — it is auto-generated from the CSV files in `data/raw/`.

**To initialize the database:**
```bash
# From project root, with venv activated
source venv/bin/activate
python -m backend.database.ingestion
```

Expected output:
```
=== Starting ParallaX Road Safety Data Ingestion ===
Police stations seeded: 33
DS3: 19 rows loaded (years: 2007–2025)
DS1: 58 rows loaded from accident_stats_2024.csv
DS4: 39 rows loaded
DS2: 33 rows loaded
DS5: 33 rows loaded
Blackspots: 64 records loaded
Loading CAS alerts — this may take 30-60 seconds...
CAS: 207,575 valid unique records after deduplication
=== Ingestion Complete ===
```

> The ingestion is **idempotent** — running it again will skip already-ingested sources unless `--force` is passed.

---

## 11. Start the Complete Application

### Option A — One-command startup (recommended)
```bash
# From project root
bash start.sh
```

This script automatically:
1. Activates the virtual environment
2. Installs any missing dependencies
3. Runs data ingestion if the database is empty
4. Starts the backend on port 8000
5. Starts the frontend on port 3000

### Option B — Manual startup (two terminals)

**Terminal 1 — Backend:**
```bash
cd ParallaX_Road_Safety_Intelligence_Platform
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd ParallaX_Road_Safety_Intelligence_Platform/frontend
npm run dev
```

---

## 12. Dashboard and API URLs

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **Swagger API Docs** | http://localhost:8000/api/docs |
| **Health Check** | http://localhost:8000/api/health |

**Dashboard pages:**
- `/overview` — KPIs, trends, agent status
- `/analytics` — Station-level accident analytics
- `/gismap` — Interactive Leaflet map (choropleth + blackspots + CAS heatmap)
- `/blackspots` — 64 Official BTP blackspot browser
- `/cas` — CAS alert analysis
- `/agents` — AI agent execution interface
- `/recommendations` — Safety recommendations
- `/data-sources` — Data quality reports
- `/assistant` — AI Q&A interface

---

## 13. IBM Granite Configuration

IBM Granite is used as the **reasoning bridge** — it converts numerical ML outputs into natural-language reports, blackspot characterizations, maintenance alerts, and intervention documents.

**To enable:**
1. Create an IBM Cloud account at https://cloud.ibm.com
2. Provision IBM watsonx.ai (Lite tier available)
3. Create a project and note your Project ID
4. Generate an API key at https://cloud.ibm.com/iam/apikeys
5. Add credentials to `backend/.env`:
   ```
   WATSONX_API_KEY=your_key_here
   WATSONX_PROJECT_ID=your_project_id_here
   ```
6. Restart the backend

**Without credentials:** All features work using the deterministic fallback, clearly labeled in the UI. No functionality is blocked.

---

## Known Limitations

- Station circles on the GIS map use approximate central coordinates. Exact police jurisdiction boundary polygons require a verified GeoJSON dataset from Karnataka Police / data.gov.in.
- Road condition analysis (Agent 3) is in awaiting-data state — no road surface images are included in the current dataset. The agent correctly reports this and shows CAS overspeed data as a proxy.
- The CAS alert dataset covers only Feb–Jul 2018. Alerts are driving-safety indicators, not confirmed accidents.
- IBM Granite requires valid watsonx.ai credentials. The deterministic fallback is fully functional without them.
- Performance has been verified on this machine. Cross-machine reproducibility depends on matching Python 3.12 and Node.js 20+ versions.

---

## Verified Test Results (on this machine)

```
✓ Backend health:          {"status":"healthy","team":"ParallaX","problem":"PS8"}
✓ Accident records:        232 station-level records (2018–2024)
✓ Official blackspots:     64 (all geocoded)
✓ CAS alerts:              207,575 valid records ingested
✓ Annual data:             19 years (2007–2025)
✓ 2024 citywide total:     4,769 accidents, 869 fatal, 894 killed
✓ Agent 1 — Risk:          34 stations analyzed, top = KR Pura (HIGH, 100.0)
✓ Agent 2 — Blackspot:     64 official locations, 28 stations covered
✓ Agent 3 — Road Cond:     Correctly reports unavailable + proxy data
✓ Agent 4 — Recs:          58 evidence-based recommendations generated
✓ Agent 5 — Dashboard:     Summary + Q&A verified working
✓ Frontend build:          9 routes compiled (npm run build PASSED)
✓ API docs:                Available at /api/docs
```

---

*ParallaX | IBM Hackathon 2026 | Problem Statement 8*  
*Team ParallaX — Bengaluru Road Safety & Accident Risk Intelligence Platform*
