"""
ParallaX | Bengaluru Road Safety & Accident Risk Intelligence Platform
FastAPI Backend — Main Application
Team: ParallaX | Problem Statement 8 | IBM Hackathon
"""
import os, json, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database.db import engine, SessionLocal, Base, get_db
from .database.models import (
    AccidentStatistic, HistoricalAccidentStat, OfficialBlackspot,
    CasAlertAggregated, CasAlertSpatial, RiskAssessment,
    SafetyRecommendation, AgentExecutionLog, DataSourceMetadata, DataQualityReport
)
from .agents.accident_risk_agent import AccidentRiskAgent
from .agents.blackspot_agent import BlackspotAgent
from .agents.road_condition_agent import RoadConditionAgent
from .agents.recommendation_agent import RecommendationAgent
from .agents.dashboard_agent import DashboardAgent
from .agents.orchestrator import RoadSafetyOrchestrator
from .services.granite_client import GraniteClient

# Initialize once
orchestrator = RoadSafetyOrchestrator()
granite = GraniteClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ParallaX Road Safety Platform...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from .database.ingestion import run_all_ingestion
        count = db.query(AccidentStatistic).count()
        if count == 0:
            logger.info("No data found — running ingestion...")
            run_all_ingestion(force=False)
        else:
            logger.info(f"Database ready: {count} accident records found")
        # Ensure risk assessments calculated
        ra_count = db.query(RiskAssessment).count()
        if ra_count == 0:
            logger.info("Calculating initial risk assessments...")
            orchestrator.risk_agent.analyze(db)
            db.commit()
    except Exception as e:
        logger.error(f"Startup error: {e}")
    finally:
        db.close()
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="ParallaX Road Safety Intelligence API",
    description="Bengaluru Road Safety & Accident Risk Intelligence Platform — Team ParallaX",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    acc_count = db.query(AccidentStatistic).filter_by(is_summary_row=False).count()
    bs_count = db.query(OfficialBlackspot).count()
    cas_count = db.query(func.sum(CasAlertAggregated.alert_count)).scalar() or 0
    return {"status": "healthy", "team": "ParallaX", "problem": "PS8",
            "records": {"accidents": acc_count, "blackspots": bs_count, "cas_alerts": int(cas_count)},
            "granite": granite.status}

# ═══════════════════════════════════════════════════════════
# DASHBOARD SUMMARY
# ═══════════════════════════════════════════════════════════
@app.get("/api/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    agent = DashboardAgent()
    return agent.get_summary(db)

# ═══════════════════════════════════════════════════════════
# ACCIDENTS
# ═══════════════════════════════════════════════════════════
@app.get("/api/accidents/annual")
def annual_trends(db: Session = Depends(get_db)):
    agent = DashboardAgent()
    return {"data": agent.get_annual_trends(db), "source": "Historical Annual Accident Statistics"}

@app.get("/api/accidents/by-station")
def accidents_by_station(year: int = Query(None), zone: str = Query(None),
                          limit: int = Query(50), db: Session = Depends(get_db)):
    yr = year or db.query(func.max(AccidentStatistic.year)).filter(
        AccidentStatistic.is_summary_row == False).scalar() or 2024
    q = db.query(AccidentStatistic).filter(
        AccidentStatistic.year == yr, AccidentStatistic.is_summary_row == False)
    if zone:
        q = q.filter(AccidentStatistic.zone == zone)
    rows = q.order_by(desc(AccidentStatistic.total_accidents)).limit(limit).all()
    return {"year": yr, "data": [
        {"police_station": r.police_station, "zone": r.zone or "", "year": r.year,
         "fatal_accidents": r.fatal_accidents or 0, "non_fatal_accidents": r.non_fatal_accidents or 0,
         "total_accidents": r.total_accidents or 0, "people_killed": r.people_killed or 0,
         "people_injured": r.people_injured or 0} for r in rows]}

@app.get("/api/accidents/trends")
def accident_trends(police_station: str = Query(None), db: Session = Depends(get_db)):
    if police_station:
        agent = AccidentRiskAgent()
        return agent.get_trend_analysis(db, police_station)
    return {"data": DashboardAgent().get_annual_trends(db)}

@app.get("/api/accidents/severity")
def severity_analysis(year: int = Query(None), db: Session = Depends(get_db)):
    yr = year or db.query(func.max(AccidentStatistic.year)).filter(
        AccidentStatistic.is_summary_row == False).scalar() or 2024
    rows = db.query(AccidentStatistic).filter(
        AccidentStatistic.year == yr, AccidentStatistic.is_summary_row == False
    ).order_by(desc(AccidentStatistic.fatal_accidents)).all()
    total_f = sum(r.fatal_accidents or 0 for r in rows)
    total_nf = sum(r.non_fatal_accidents or 0 for r in rows)
    total_t = sum(r.total_accidents or 0 for r in rows)
    return {"year": yr, "total_fatal": total_f, "total_non_fatal": total_nf, "total": total_t,
            "fatality_rate_pct": round(total_f / total_t * 100, 1) if total_t else 0,
            "note": "Station-level aggregate. Excludes summary rows."}

@app.get("/api/accidents/reconciliation")
def data_reconciliation(db: Session = Depends(get_db)):
    """Transparent data reconciliation report."""
    reconciliation = []
    for year in [2018, 2019, 2021, 2022, 2023, 2024]:
        hist = db.query(HistoricalAccidentStat).filter_by(year=year).first()
        station_agg = db.query(func.sum(AccidentStatistic.fatal_accidents)).filter(
            AccidentStatistic.year == year, AccidentStatistic.is_summary_row == False).scalar() or 0
        if hist:
            diff = int(station_agg) - hist.fatal_accidents
            reconciliation.append({
                "year": year, "historical_dataset_fatal": hist.fatal_accidents,
                "station_level_aggregate_fatal": int(station_agg),
                "difference": diff,
                "status": "MATCH" if abs(diff) <= 5 else "DISCREPANCY",
                "note": "Minor discrepancies are expected between citywide totals and station-level aggregates"
            })
    return {"reconciliation": reconciliation,
            "methodology_note": "Both datasets preserved. Discrepancies documented transparently."}

# ═══════════════════════════════════════════════════════════
# BLACKSPOTS
# ═══════════════════════════════════════════════════════════
@app.get("/api/blackspots")
def get_blackspots(police_station: str = Query(None), location_type: str = Query(None),
                   db: Session = Depends(get_db)):
    q = db.query(OfficialBlackspot)
    if police_station:
        q = q.filter(OfficialBlackspot.police_station == police_station)
    if location_type:
        q = q.filter(OfficialBlackspot.location_type.ilike(f"%{location_type}%"))
    bss = q.order_by(OfficialBlackspot.police_station, OfficialBlackspot.blackspot_id).all()
    return {"total": len(bss), "blackspots": [
        {"blackspot_id": b.blackspot_id, "police_station": b.police_station,
         "original_location_description": b.original_location_description,
         "normalized_location_name": b.normalized_location_name,
         "road_name": b.road_name, "location_type": b.location_type,
         "source": b.source, "identification_year": b.identification_year,
         "latitude": b.latitude, "longitude": b.longitude,
         "geocoding_status": b.geocoding_status, "verification_status": b.verification_status}
        for b in bss]}

@app.get("/api/blackspots/{blackspot_id}")
def get_blackspot_detail(blackspot_id: str, db: Session = Depends(get_db)):
    bs = db.query(OfficialBlackspot).filter_by(blackspot_id=blackspot_id).first()
    if not bs:
        raise HTTPException(404, "Blackspot not found")
    station_stat = db.query(AccidentStatistic).filter(
        AccidentStatistic.police_station == bs.police_station,
        AccidentStatistic.is_summary_row == False
    ).order_by(desc(AccidentStatistic.year)).first()
    return {"blackspot_id": bs.blackspot_id, "police_station": bs.police_station,
            "original_location_description": bs.original_location_description,
            "normalized_location_name": bs.normalized_location_name,
            "road_name": bs.road_name, "location_type": bs.location_type,
            "source": bs.source, "identification_year": bs.identification_year,
            "latitude": bs.latitude, "longitude": bs.longitude,
            "geocoding_status": bs.geocoding_status, "verification_status": bs.verification_status,
            "station_latest_stats": {
                "year": station_stat.year if station_stat else None,
                "total_accidents": station_stat.total_accidents if station_stat else None,
                "fatal_accidents": station_stat.fatal_accidents if station_stat else None
            }}

# ═══════════════════════════════════════════════════════════
# MAP DATA
# ═══════════════════════════════════════════════════════════
@app.get("/api/map/police-stations")
def map_police_stations(year: int = Query(None), db: Session = Depends(get_db)):
    yr = year or db.query(func.max(AccidentStatistic.year)).filter(
        AccidentStatistic.is_summary_row == False).scalar() or 2024
    risk_rows = db.query(RiskAssessment).all()
    risk_map = {r.police_station: r for r in risk_rows}
    stats = db.query(AccidentStatistic).filter(
        AccidentStatistic.year == yr, AccidentStatistic.is_summary_row == False).all()
    from .database.ingestion import STATION_COORDINATES, STATION_ZONE_MAP
    result = []
    for stat in stats:
        coords = STATION_COORDINATES.get(stat.police_station, (12.9716, 77.5946))
        ra = risk_map.get(stat.police_station)
        result.append({
            "police_station": stat.police_station,
            "zone": stat.zone or STATION_ZONE_MAP.get(stat.police_station, ""),
            "lat": coords[0], "lng": coords[1],
            "total_accidents": stat.total_accidents or 0,
            "fatal_accidents": stat.fatal_accidents or 0,
            "non_fatal_accidents": stat.non_fatal_accidents or 0,
            "people_killed": stat.people_killed or 0,
            "people_injured": stat.people_injured or 0,
            "risk_score": ra.risk_score if ra else 0,
            "risk_tier": ra.risk_tier if ra else "LOW",
            "blackspot_count": ra.blackspot_count if ra else 0,
            "yoy_change_pct": ra.yoy_change_pct if ra else 0,
            "year": yr
        })
    return {"year": yr, "stations": result}

@app.get("/api/map/blackspots")
def map_blackspots(db: Session = Depends(get_db)):
    agent = BlackspotAgent()
    return {"blackspots": agent.get_map_markers(db)}

@app.get("/api/map/cas-alerts")
def map_cas_alerts(alarm_type: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(CasAlertSpatial)
    rows = q.order_by(desc(CasAlertSpatial.alert_count)).limit(2000).all()
    return {"heatmap_points": [
        {"lat": r.lat_bin + 0.01, "lng": r.lng_bin + 0.01,
         "intensity": r.alert_count, "overspeed": r.overspeed_count}
        for r in rows],
        "note": "CAS alerts aggregated into 0.02° spatial bins (~2km). Not confirmed accidents."}

# ═══════════════════════════════════════════════════════════
# CAS ALERTS
# ═══════════════════════════════════════════════════════════
@app.get("/api/cas/summary")
def cas_summary(db: Session = Depends(get_db)):
    return DashboardAgent().get_cas_summary(db)

@app.get("/api/cas/by-ward")
def cas_by_ward(limit: int = Query(50), db: Session = Depends(get_db)):
    rows = db.query(CasAlertAggregated.ward_name,
        func.sum(CasAlertAggregated.alert_count).label("total"),
        func.sum(CasAlertAggregated.overspeed_count).label("overspeed"),
        func.avg(CasAlertAggregated.avg_speed).label("avg_speed")
    ).group_by(CasAlertAggregated.ward_name).order_by(
        func.sum(CasAlertAggregated.alert_count).desc()).limit(limit).all()
    return {"data": [{"ward": r.ward_name, "total_alerts": int(r.total or 0),
                      "overspeed_alerts": int(r.overspeed or 0),
                      "avg_speed": round(float(r.avg_speed or 0), 1)} for r in rows]}

@app.get("/api/cas/by-alarm-type")
def cas_by_alarm_type(db: Session = Depends(get_db)):
    rows = db.query(CasAlertAggregated.alarm_type,
        func.sum(CasAlertAggregated.alert_count).label("total")
    ).group_by(CasAlertAggregated.alarm_type).order_by(
        func.sum(CasAlertAggregated.alert_count).desc()).all()
    return {"data": [{"alarm_type": r.alarm_type, "count": int(r.total or 0)} for r in rows]}

@app.get("/api/cas/overspeeding")
def cas_overspeeding(db: Session = Depends(get_db)):
    rows = db.query(CasAlertAggregated).filter(
        CasAlertAggregated.alarm_type == "Overspeed"
    ).order_by(desc(CasAlertAggregated.overspeed_count)).all()
    return {"total_overspeed_alerts": sum(r.overspeed_count for r in rows),
            "data": [{"ward": r.ward_name, "overspeed_count": r.overspeed_count,
                      "avg_speed": round(r.avg_speed or 0, 1),
                      "max_speed": r.max_speed or 0} for r in rows]}

# ═══════════════════════════════════════════════════════════
# RISK
# ═══════════════════════════════════════════════════════════
@app.get("/api/risk/stations")
def risk_stations(db: Session = Depends(get_db)):
    rows = db.query(RiskAssessment).order_by(desc(RiskAssessment.risk_score)).all()
    if not rows:
        # Calculate on demand
        agent = AccidentRiskAgent()
        result = agent.analyze(db)
        db.commit()
        rows = db.query(RiskAssessment).order_by(desc(RiskAssessment.risk_score)).all()
    return {"data": [
        {"police_station": r.police_station, "zone": r.zone, "risk_score": r.risk_score,
         "risk_tier": r.risk_tier, "latest_total": r.latest_year_total,
         "latest_fatal": r.latest_year_fatal, "yoy_change_pct": r.yoy_change_pct,
         "blackspot_count": r.blackspot_count, "methodology": r.methodology} for r in rows]}

# ═══════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════
@app.get("/api/recommendations")
def get_recommendations(police_station: str = Query(None), limit: int = Query(50),
                        db: Session = Depends(get_db)):
    q = db.query(SafetyRecommendation)
    if police_station:
        q = q.filter(SafetyRecommendation.police_station == police_station)
    recs = q.order_by(SafetyRecommendation.priority_rank).limit(limit).all()
    if not recs:
        agent = RecommendationAgent()
        result = agent.analyze(db, police_station)
        db.commit()
        recs = db.query(SafetyRecommendation).order_by(SafetyRecommendation.priority_rank).limit(limit).all()
    return {"total": len(recs), "recommendations": [
        {"id": r.id, "police_station": r.police_station, "priority_rank": r.priority_rank,
         "recommendation_type": r.recommendation_type, "recommendation_text": r.recommendation_text,
         "evidence_summary": r.evidence_summary, "responsible_authority": r.responsible_authority,
         "evidence_strength": r.evidence_strength, "data_limitations": r.data_limitations} for r in recs]}

# ═══════════════════════════════════════════════════════════
# AI AGENTS
# ═══════════════════════════════════════════════════════════
@app.get("/api/agents")
def list_agents():
    return {"agents": [
        {"id": "accident_risk", "name": "Accident Risk Prediction Agent",
         "description": "Analyzes historical accident patterns and CAS indicators to identify elevated-risk areas.",
         "inputs": ["Accident statistics (2018-2024)", "CAS alert data", "Official blackspot data"],
         "outputs": ["Risk scores per station", "SHAP-equivalent factor attribution", "YoY trends"],
         "status": "active", "algorithm": "Normalized severity-weighted scoring (60% fatal, 40% total)"},
        {"id": "blackspot", "name": "Blackspot Identification Agent",
         "description": "Manages official BTP blackspots and identifies data-derived high-accident areas.",
         "inputs": ["64 official BTP blackspot locations", "Accident statistics"],
         "outputs": ["Official blackspot registry", "Station-level accident rankings"],
         "status": "active", "algorithm": "Official designation + frequency ranking"},
        {"id": "road_condition", "name": "Road Condition Analysis Agent",
         "description": "Analyzes road condition data. Currently reports unavailable — no image data supplied.",
         "inputs": ["Road surface images (not yet available)", "Overspeed CAS alerts (proxy)"],
         "outputs": ["Condition status (unavailable)", "Overspeed alert concentration as proxy"],
         "status": "awaiting_data", "algorithm": "YOLOv8 CV (planned) / Overspeed proxy (current)"},
        {"id": "recommendation", "name": "Road Safety Recommendation Agent",
         "description": "Generates evidence-based intervention recommendations from validated agent outputs.",
         "inputs": ["Risk assessments", "Official blackspots", "CAS overspeeding data"],
         "outputs": ["Prioritized intervention recommendations with evidence basis"],
         "status": "active", "algorithm": "Intervention knowledge base + risk tier mapping"},
        {"id": "dashboard", "name": "Road Safety Analytics Dashboard Agent",
         "description": "Coordinates all agent outputs for unified analytics and Q&A.",
         "inputs": ["All agent outputs", "Natural language queries"],
         "outputs": ["Dashboard summary", "Analytics", "Granite-enhanced Q&A"],
         "status": "active", "algorithm": "Aggregation + IBM Granite LLM (when available)"}
    ], "granite_status": granite.status}

@app.post("/api/agents/analyze")
def run_agent_analysis(request: dict, db: Session = Depends(get_db)):
    police_station = request.get("police_station")
    year = request.get("year")
    agent_id = request.get("agent_id", "all")
    gc = granite if granite.available else None

    if agent_id == "accident_risk":
        return AccidentRiskAgent().analyze(db, police_station, year)
    elif agent_id == "blackspot":
        return BlackspotAgent().analyze(db, police_station)
    elif agent_id == "road_condition":
        return RoadConditionAgent().analyze(db, police_station)
    elif agent_id == "recommendation":
        return RecommendationAgent().analyze(db, police_station, gc)
    elif agent_id == "dashboard":
        return DashboardAgent().analyze(db)
    else:
        return orchestrator.run_full_analysis(db, police_station, year, gc)

# ═══════════════════════════════════════════════════════════
# ASSISTANT (Q&A)
# ═══════════════════════════════════════════════════════════
@app.post("/api/assistant/query")
def assistant_query(request: dict, db: Session = Depends(get_db)):
    question = request.get("question", "").strip()
    if not question:
        raise HTTPException(400, "Question is required")
    gc = granite if granite.available else None
    result = DashboardAgent().answer_query(db, question, gc)
    return result

# ═══════════════════════════════════════════════════════════
# DATA SOURCES & QUALITY
# ═══════════════════════════════════════════════════════════
@app.get("/api/data-sources")
def data_sources(db: Session = Depends(get_db)):
    sources = db.query(DataSourceMetadata).all()
    return {"data_sources": [
        {"name": s.source_name, "file_path": s.file_path, "record_count": s.record_count,
         "date_coverage": s.date_coverage, "available_fields": s.available_fields,
         "validation_status": s.validation_status, "known_limitations": s.known_limitations,
         "last_processed": str(s.last_processed_at) if s.last_processed_at else None}
        for s in sources]}

@app.get("/api/data-quality")
def data_quality(db: Session = Depends(get_db)):
    reports = db.query(DataQualityReport).order_by(DataQualityReport.created_at.desc()).all()
    return {"reports": [
        {"source": r.source_name, "check": r.check_name, "result": r.check_result,
         "details": r.details, "timestamp": str(r.created_at)} for r in reports]}

@app.get("/api/agent-logs")
def agent_logs(limit: int = Query(50), db: Session = Depends(get_db)):
    logs = db.query(AgentExecutionLog).order_by(
        AgentExecutionLog.created_at.desc()).limit(limit).all()
    return {"logs": [
        {"agent": l.agent_name, "task": l.task_description, "status": l.status,
         "execution_ms": l.execution_time_ms, "timestamp": str(l.created_at),
         "error": l.error_message} for l in logs]}
