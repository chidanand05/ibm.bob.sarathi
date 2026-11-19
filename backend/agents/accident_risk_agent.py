"""
ParallaX | Agent 1 — Accident Risk Prediction Agent
Analyzes historical accident patterns, CAS indicators, and pedestrian context
to identify elevated accident-risk areas.
"""
import json
import time
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database.models import (
    AccidentStatistic, HistoricalAccidentStat, CasAlertAggregated,
    OfficialBlackspot, RiskAssessment, AgentExecutionLog
)

logger = logging.getLogger(__name__)

# Risk scoring weights (documented, configurable)
FATAL_WEIGHT = 0.60
TOTAL_WEIGHT = 0.40

# Pedestrian-related location type keywords for context
PEDESTRIAN_LOCATION_TYPES = ["bus stop", "pedestrian infrastructure", "metro station", "school zone", "educational"]


class AccidentRiskAgent:
    """
    Agent 1: Accident Risk Prediction Agent.
    Calculates transparent risk scores per police station using:
    - Fatal accident frequency (60% weight)
    - Total accident frequency (40% weight)
    - CAS alert concentration (supplementary indicator)
    - Blackspot presence (supplementary indicator)
    - Pedestrian infrastructure context from blackspot data
    
    IMPORTANT: Risk scores are analytical rankings, not validated accident probabilities.
    """

    name = "Accident Risk Prediction Agent"
    agent_id = "accident_risk"

    def analyze(self, db: Session, police_station: Optional[str] = None,
                year: Optional[int] = None) -> dict:
        start_time = time.time()
        log = AgentExecutionLog(
            agent_name=self.name,
            task_description=f"Risk analysis for station={police_station}, year={year}",
            input_params=json.dumps({"police_station": police_station, "year": year}),
            status="running"
        )
        db.add(log)
        db.flush()

        try:
            result = self._run_analysis(db, police_station, year)
            log.status = "completed"
            log.output_summary = json.dumps({"stations_analyzed": len(result.get("stations", []))})
            log.execution_time_ms = int((time.time() - start_time) * 1000)
            db.commit()
            return result
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.execution_time_ms = int((time.time() - start_time) * 1000)
            db.commit()
            raise

    def _run_analysis(self, db: Session, police_station: Optional[str],
                      year: Optional[int]) -> dict:
        # Get latest available year if not specified
        latest_year = year or self._get_latest_year(db)
        comparison_year = latest_year - 1

        # Fetch station-level stats for target year (excluding summary rows)
        query = db.query(AccidentStatistic).filter(
            AccidentStatistic.year == latest_year,
            AccidentStatistic.is_summary_row == False
        )
        if police_station:
            query = query.filter(AccidentStatistic.police_station == police_station)

        stats = query.all()

        if not stats:
            return {"error": "No accident data available for the requested parameters",
                    "year": latest_year, "stations": []}

        # Normalize for risk scoring
        fatal_values = [s.fatal_accidents for s in stats if s.fatal_accidents is not None]
        total_values = [s.total_accidents for s in stats if s.total_accidents is not None]

        max_fatal = max(fatal_values) if fatal_values else 1
        max_total = max(total_values) if total_values else 1

        # Fetch CAS alert counts per station (supplementary, not primary)
        cas_by_station = self._get_cas_by_station_proxy(db)

        # Fetch blackspot counts per station
        blackspot_counts = self._get_blackspot_counts(db)

        # Fetch previous year for YoY comparison
        prev_stats = {
            s.police_station: s for s in
            db.query(AccidentStatistic).filter(
                AccidentStatistic.year == comparison_year,
                AccidentStatistic.is_summary_row == False
            ).all()
        }

        station_results = []
        for s in stats:
            fatal_norm = (s.fatal_accidents or 0) / max_fatal
            total_norm = (s.total_accidents or 0) / max_total
            risk_score = round(
                (FATAL_WEIGHT * fatal_norm + TOTAL_WEIGHT * total_norm) * 100, 1
            )

            # Risk tier
            if risk_score >= 65:
                risk_tier = "HIGH"
            elif risk_score >= 45:
                risk_tier = "MEDIUM_HIGH"
            elif risk_score >= 25:
                risk_tier = "MODERATE"
            else:
                risk_tier = "LOW"

            # YoY change
            prev = prev_stats.get(s.police_station)
            yoy_change = 0.0
            if prev and prev.total_accidents and prev.total_accidents > 0:
                yoy_change = round(
                    ((s.total_accidents or 0) - prev.total_accidents) / prev.total_accidents * 100, 1
                )

            # CAS indicator (supplementary — labeled as driving-safety alerts)
            cas_count = cas_by_station.get(s.police_station, 0)
            bs_count = blackspot_counts.get(s.police_station, 0)

            # Pedestrian context — check blackspots with pedestrian types
            pedestrian_bs = self._get_pedestrian_blackspot_context(db, s.police_station)

            station_data = {
                "police_station": s.police_station,
                "zone": s.zone or "Unknown",
                "year": latest_year,
                "fatal_accidents": s.fatal_accidents or 0,
                "non_fatal_accidents": s.non_fatal_accidents or 0,
                "total_accidents": s.total_accidents or 0,
                "people_killed": s.people_killed or 0,
                "people_injured": s.people_injured or 0,
                "risk_score": risk_score,
                "risk_tier": risk_tier,
                "fatal_score_component": round(fatal_norm * 100, 1),
                "total_score_component": round(total_norm * 100, 1),
                "yoy_change_pct": yoy_change,
                "blackspot_count": bs_count,
                "cas_alert_count": cas_count,
                "pedestrian_context": pedestrian_bs,
                "data_note": "Risk score = 0.60×(normalized fatal) + 0.40×(normalized total). "
                             "Analytical ranking only, not validated probability."
            }
            station_results.append(station_data)

            # Persist risk assessment
            existing_ra = db.query(RiskAssessment).filter_by(
                police_station=s.police_station
            ).first()
            if existing_ra:
                existing_ra.risk_score = risk_score
                existing_ra.risk_tier = risk_tier
                existing_ra.latest_year_total = s.total_accidents or 0
                existing_ra.latest_year_fatal = s.fatal_accidents or 0
                existing_ra.yoy_change_pct = yoy_change
                existing_ra.blackspot_count = bs_count
                existing_ra.cas_alert_count = cas_count
                existing_ra.calculated_at = datetime.now()
            else:
                ra = RiskAssessment(
                    police_station=s.police_station,
                    zone=s.zone or "",
                    risk_score=risk_score,
                    risk_tier=risk_tier,
                    fatal_score_component=round(fatal_norm * 100, 1),
                    total_score_component=round(total_norm * 100, 1),
                    blackspot_count=bs_count,
                    cas_alert_count=cas_count,
                    latest_year_total=s.total_accidents or 0,
                    latest_year_fatal=s.fatal_accidents or 0,
                    yoy_change_pct=yoy_change,
                    methodology=f"Risk = {FATAL_WEIGHT}×fatal_norm + {TOTAL_WEIGHT}×total_norm. Year: {latest_year}"
                )
                db.add(ra)

        db.flush()

        # Sort by risk score
        station_results.sort(key=lambda x: x["risk_score"], reverse=True)

        return {
            "agent": self.name,
            "analysis_year": latest_year,
            "comparison_year": comparison_year,
            "stations_analyzed": len(station_results),
            "methodology": f"Risk Score = {FATAL_WEIGHT}×Normalized_Fatal + {TOTAL_WEIGHT}×Normalized_Total (×100). Excludes summary rows.",
            "data_limitations": [
                "Risk scores are analytical rankings based on accident frequency, not validated probabilities",
                "CAS alerts are driving-safety indicators, not confirmed accident records",
                "Pedestrian context is derived from blackspot location type, not direct pedestrian counts",
                "Station-level totals may differ slightly from citywide annual totals due to data source differences"
            ],
            "stations": station_results
        }

    def _get_latest_year(self, db: Session) -> int:
        result = db.query(func.max(AccidentStatistic.year)).filter(
            AccidentStatistic.is_summary_row == False
        ).scalar()
        return result or 2024

    def _get_cas_by_station_proxy(self, db: Session) -> dict:
        """
        Returns ward-level CAS alert counts as a proxy for station area.
        Cannot directly map wards to police stations without GIS join.
        Returns approximate totals labeled clearly as proxies.
        """
        rows = db.query(
            CasAlertAggregated.ward_name,
            func.sum(CasAlertAggregated.alert_count).label("total")
        ).group_by(CasAlertAggregated.ward_name).all()
        return {r.ward_name: r.total for r in rows}

    def _get_blackspot_counts(self, db: Session) -> dict:
        rows = db.query(
            OfficialBlackspot.police_station,
            func.count(OfficialBlackspot.id).label("count")
        ).group_by(OfficialBlackspot.police_station).all()
        return {r.police_station: r.count for r in rows}

    def _get_pedestrian_blackspot_context(self, db: Session, station: str) -> list:
        bs_list = db.query(OfficialBlackspot).filter(
            OfficialBlackspot.police_station == station
        ).all()
        pedestrian_locations = []
        for bs in bs_list:
            lt = (bs.location_type or "").lower()
            if any(p in lt for p in PEDESTRIAN_LOCATION_TYPES):
                pedestrian_locations.append({
                    "location": bs.normalized_location_name,
                    "type": bs.location_type,
                    "description": bs.original_location_description
                })
        return pedestrian_locations

    def get_trend_analysis(self, db: Session, police_station: str) -> dict:
        """Multi-year trend analysis for a specific station."""
        stats = db.query(AccidentStatistic).filter(
            AccidentStatistic.police_station == police_station,
            AccidentStatistic.is_summary_row == False
        ).order_by(AccidentStatistic.year).all()

        if not stats:
            return {"error": "No data for this station"}

        years = [s.year for s in stats]
        fatal = [s.fatal_accidents or 0 for s in stats]
        non_fatal = [s.non_fatal_accidents or 0 for s in stats]
        total = [s.total_accidents or 0 for s in stats]
        killed = [s.people_killed or 0 for s in stats]
        injured = [s.people_injured or 0 for s in stats]

        return {
            "police_station": police_station,
            "years": years,
            "fatal_accidents": fatal,
            "non_fatal_accidents": non_fatal,
            "total_accidents": total,
            "people_killed": killed,
            "people_injured": injured,
            "data_sources": list(set(s.source_dataset for s in stats))
        }
