"""
ParallaX | Agent 5 — Road Safety Analytics Dashboard Agent
Coordinates all agent outputs and provides unified analytics.
"""
import json, time, logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database.models import (
    AccidentStatistic, HistoricalAccidentStat, OfficialBlackspot,
    CasAlertAggregated, RiskAssessment, SafetyRecommendation,
    AgentExecutionLog, DataSourceMetadata
)
logger = logging.getLogger(__name__)

class DashboardAgent:
    name = "Road Safety Analytics Dashboard Agent"
    agent_id = "dashboard"

    def get_summary(self, db: Session) -> dict:
        latest_year = db.query(func.max(AccidentStatistic.year)).filter(
            AccidentStatistic.is_summary_row == False).scalar() or 2024
        # Grand totals from historical table (most reliable for citywide)
        hist = db.query(HistoricalAccidentStat).filter_by(year=latest_year).first()
        hist_2024 = db.query(HistoricalAccidentStat).filter_by(year=2024).first()
        hist_2023 = db.query(HistoricalAccidentStat).filter_by(year=2023).first()
        total_acc = hist.total_accidents if hist else 0
        fatal_acc = hist.fatal_accidents if hist else 0
        non_fatal = hist.non_fatal_accidents if hist else 0
        killed = hist.people_killed if hist else 0
        injured = hist.people_injured if hist else 0
        bs_count = db.query(OfficialBlackspot).count()
        cas_count = db.query(func.sum(CasAlertAggregated.alert_count)).scalar() or 0
        risk_counts = db.query(RiskAssessment.risk_tier, func.count(RiskAssessment.id)).group_by(
            RiskAssessment.risk_tier).all()
        risk_dist = {r[0]: r[1] for r in risk_counts}
        return {
            "total_accidents": total_acc, "fatal_accidents": fatal_acc,
            "non_fatal_accidents": non_fatal, "people_killed": killed,
            "people_injured": injured, "official_blackspots": bs_count,
            "cas_alert_records": int(cas_count), "latest_year": latest_year,
            "risk_distribution": risk_dist,
            "source_note": f"Accident data from historical annual statistics dataset. Year: {latest_year}"
        }

    def get_annual_trends(self, db: Session) -> list:
        rows = db.query(HistoricalAccidentStat).order_by(HistoricalAccidentStat.year).all()
        return [{"year": r.year, "fatal_accidents": r.fatal_accidents,
                 "non_fatal_accidents": r.non_fatal_accidents, "total_accidents": r.total_accidents,
                 "people_killed": r.people_killed, "people_injured": r.people_injured} for r in rows]

    def get_top_stations(self, db: Session, year: int = None, limit: int = 15) -> list:
        yr = year or db.query(func.max(AccidentStatistic.year)).filter(
            AccidentStatistic.is_summary_row == False).scalar() or 2024
        rows = db.query(AccidentStatistic).filter(
            AccidentStatistic.year == yr, AccidentStatistic.is_summary_row == False
        ).order_by(desc(AccidentStatistic.total_accidents)).limit(limit).all()
        return [{"police_station": r.police_station, "zone": r.zone or "",
                 "total_accidents": r.total_accidents or 0, "fatal_accidents": r.fatal_accidents or 0,
                 "non_fatal_accidents": r.non_fatal_accidents or 0,
                 "people_killed": r.people_killed or 0, "year": yr} for r in rows]

    def get_zone_summary(self, db: Session, year: int = None) -> list:
        yr = year or db.query(func.max(AccidentStatistic.year)).filter(
            AccidentStatistic.is_summary_row == False).scalar() or 2024
        rows = db.query(
            AccidentStatistic.zone,
            func.sum(AccidentStatistic.total_accidents).label("total"),
            func.sum(AccidentStatistic.fatal_accidents).label("fatal"),
            func.sum(AccidentStatistic.non_fatal_accidents).label("non_fatal"),
            func.sum(AccidentStatistic.people_killed).label("killed")
        ).filter(AccidentStatistic.year == yr, AccidentStatistic.is_summary_row == False,
                 AccidentStatistic.zone != "").group_by(AccidentStatistic.zone).all()
        return [{"zone": r.zone, "total_accidents": int(r.total or 0), "fatal_accidents": int(r.fatal or 0),
                 "non_fatal_accidents": int(r.non_fatal or 0), "people_killed": int(r.killed or 0)} for r in rows]

    def get_cas_summary(self, db: Session) -> dict:
        alarm_rows = db.query(
            CasAlertAggregated.alarm_type,
            func.sum(CasAlertAggregated.alert_count).label("total")
        ).group_by(CasAlertAggregated.alarm_type).order_by(func.sum(CasAlertAggregated.alert_count).desc()).all()
        ward_rows = db.query(
            CasAlertAggregated.ward_name,
            func.sum(CasAlertAggregated.alert_count).label("total"),
            func.sum(CasAlertAggregated.overspeed_count).label("overspeed")
        ).group_by(CasAlertAggregated.ward_name).order_by(func.sum(CasAlertAggregated.alert_count).desc()).limit(20).all()
        total = db.query(func.sum(CasAlertAggregated.alert_count)).scalar() or 0
        return {
            "total_alerts": int(total),
            "alarm_distribution": [{"alarm_type": r.alarm_type, "count": int(r.total)} for r in alarm_rows],
            "top_wards": [{"ward": r.ward_name, "total_alerts": int(r.total),
                           "overspeed_alerts": int(r.overspeed or 0)} for r in ward_rows],
            "data_note": "CAS alerts are driving-safety indicators (Feb-Jul 2018), NOT confirmed accidents."
        }

    def answer_query(self, db: Session, question: str, granite_client=None) -> dict:
        """Natural language query handler — calculates from DB, optionally enhances with Granite."""
        q = question.lower()
        data = {}
        if any(w in q for w in ["highest", "most", "top", "dangerous", "risk"]):
            stations = self.get_top_stations(db, limit=5)
            data["answer_type"] = "top_stations"
            data["stations"] = stations
            data["computed_answer"] = f"Top 5 stations by accident count: " + ", ".join(
                f"{s['police_station']} ({s['total_accidents']})" for s in stations)
        elif any(w in q for w in ["fatal", "death", "killed", "trend", "year"]):
            trends = self.get_annual_trends(db)
            recent = trends[-5:] if trends else []
            data["answer_type"] = "annual_trends"
            data["trends"] = recent
            data["computed_answer"] = f"Recent fatal accident trend: " + ", ".join(
                f"{t['year']}: {t['fatal_accidents']}" for t in recent)
        elif any(w in q for w in ["blackspot", "black spot"]):
            bs_by_station = db.query(OfficialBlackspot.police_station,
                func.count(OfficialBlackspot.id).label("cnt")
            ).group_by(OfficialBlackspot.police_station).order_by(
                func.count(OfficialBlackspot.id).desc()).limit(5).all()
            data["answer_type"] = "blackspot_summary"
            data["top_stations"] = [{"station": r.police_station, "blackspot_count": r.cnt} for r in bs_by_station]
            data["total_blackspots"] = db.query(OfficialBlackspot).count()
            data["computed_answer"] = f"Total official blackspots: {data['total_blackspots']}. " + \
                "Top stations: " + ", ".join(f"{r.police_station} ({r.cnt})" for r in bs_by_station[:3])
        elif any(w in q for w in ["cas", "alert", "overspeed", "speed"]):
            cas = self.get_cas_summary(db)
            data["answer_type"] = "cas_summary"
            data["alarm_distribution"] = cas["alarm_distribution"]
            data["top_wards"] = cas["top_wards"][:5]
            data["computed_answer"] = f"Total CAS alerts: {cas['total_alerts']}. " + \
                "Most common type: " + (cas["alarm_distribution"][0]["alarm_type"] if cas["alarm_distribution"] else "N/A")
        elif any(w in q for w in ["zone", "division", "area"]):
            zones = self.get_zone_summary(db)
            data["answer_type"] = "zone_summary"
            data["zones"] = zones
            data["computed_answer"] = "Zone breakdown: " + ", ".join(
                f"{z['zone']}: {z['total_accidents']} accidents" for z in zones)
        else:
            summary = self.get_summary(db)
            data["answer_type"] = "general_summary"
            data["summary"] = summary
            data["computed_answer"] = (
                f"Bengaluru road safety overview: {summary['total_accidents']} total accidents "
                f"({summary['latest_year']}), {summary['fatal_accidents']} fatal, "
                f"{summary['people_killed']} people killed, {summary['official_blackspots']} official blackspots."
            )
        # Try Granite enhancement
        if granite_client:
            try:
                enhanced = granite_client.enhance_answer(question, data["computed_answer"], data)
                data["granite_response"] = enhanced
                data["granite_used"] = True
            except Exception as e:
                data["granite_error"] = str(e)
                data["granite_used"] = False
        else:
            data["granite_used"] = False
        data["question"] = question
        return data

    def analyze(self, db: Session, **kwargs) -> dict:
        log = AgentExecutionLog(agent_name=self.name, task_description="Dashboard summary",
            input_params="{}", status="running")
        db.add(log); db.flush()
        result = {"agent": self.name, "summary": self.get_summary(db),
                  "top_stations": self.get_top_stations(db, limit=10),
                  "zone_summary": self.get_zone_summary(db),
                  "cas_summary": self.get_cas_summary(db)}
        log.status = "completed"; log.execution_time_ms = 0; db.commit()
        return result
