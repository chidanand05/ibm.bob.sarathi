"""
ParallaX | Agent 4 — Road Safety Recommendation Agent
Generates evidence-based road safety recommendations from validated agent outputs.
"""
import json
import time
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database.models import (
    AccidentStatistic, OfficialBlackspot, RiskAssessment,
    SafetyRecommendation, AgentExecutionLog, CasAlertAggregated
)

logger = logging.getLogger(__name__)

# Intervention knowledge base: risk factor → intervention type → details
INTERVENTION_KB = {
    "HIGH_FATAL_RATE": {
        "intervention": "Advanced warning signage and speed enforcement",
        "description": "Install advanced warning signs 500m before high-risk stretch. "
                       "Deploy speed monitoring equipment. Consider speed humps on approach roads.",
        "authority": "BBMP Traffic Engineering Cell / Bengaluru Traffic Police",
        "evidence_basis": "High fatal accident rate indicates inadequate warning time for road users"
    },
    "HIGH_TOTAL_ACCIDENTS": {
        "intervention": "Junction redesign and traffic signal optimization",
        "description": "Review traffic signal phasing at key junctions. "
                       "Consider channelization at complex intersections. "
                       "Improve road markings and lane discipline signage.",
        "authority": "BBMP Roads Department / BDA",
        "evidence_basis": "High total accident concentration requires junction-level intervention"
    },
    "OFFICIAL_BLACKSPOT": {
        "intervention": "Priority road-safety audit and targeted treatment",
        "description": "Conduct formal road safety audit at all BTP-designated blackspot locations. "
                       "Implement location-specific treatments: improved lighting, guardrails, "
                       "delineators, and pedestrian crossing infrastructure.",
        "authority": "Bengaluru Traffic Police / BBMP",
        "evidence_basis": "Location officially designated by Bengaluru Traffic Police as high-risk"
    },
    "FLYOVER_RAMP": {
        "intervention": "Delineation, lighting and speed calming on ramps",
        "description": "Install reflective delineators on ramp approaches. "
                       "Improve overhead lighting on flyover sections. "
                       "Review speed limits on approach and exit ramps.",
        "authority": "BBMP / BMRCL / NHAI",
        "evidence_basis": "Flyover ramp locations in BTP blackspot list indicate elevated risk"
    },
    "BUS_STOP": {
        "intervention": "Pedestrian infrastructure and lighting at bus stops",
        "description": "Install proper bus bays to separate bus from moving traffic. "
                       "Add pedestrian crossings and lighting at bus stop locations. "
                       "Consider bus stop relocation from sharp curves or intersections.",
        "authority": "BMTC / BBMP",
        "evidence_basis": "Bus stop locations generate pedestrian-vehicle conflicts"
    },
    "SCHOOL_ZONE": {
        "intervention": "School zone safety measures",
        "description": "Install school zone markings, speed reduction signs, and crossing guards. "
                       "Restrict heavy vehicle movement during school hours. "
                       "Add speed humps on approach roads to school gates.",
        "authority": "BBMP / Traffic Police / School Management",
        "evidence_basis": "School proximity creates pedestrian vulnerability, especially for children"
    },
    "JUNCTION": {
        "intervention": "Junction safety improvement",
        "description": "Install advanced directional signage. Review signal timing. "
                       "Add pedestrian countdown signals where absent. "
                       "Consider traffic circle or channelization for complex junctions.",
        "authority": "BBMP Traffic Engineering",
        "evidence_basis": "Junction-type blackspot location indicates intersection conflict"
    },
    "BRIDGE": {
        "intervention": "Bridge approach safety improvements",
        "description": "Install bridge approach warning signs and speed calming. "
                       "Add crash barriers and guardrails on bridge approaches. "
                       "Improve lane marking visibility on bridge deck.",
        "authority": "BBMP / PWD / KRDCL",
        "evidence_basis": "Bridge locations in BTP blackspot list indicate structural risk area"
    },
    "OVERSPEED_ALERTS": {
        "intervention": "Speed enforcement and traffic calming",
        "description": "Deploy speed cameras at top overspeed alert wards. "
                       "Install speed management devices (rumble strips, chicanes) on identified corridors. "
                       "Increase patrol frequency during peak alert hours.",
        "authority": "Bengaluru Traffic Police",
        "evidence_basis": "High CAS overspeed alert concentration indicates systemic speeding behaviour"
    },
    "YOY_INCREASE": {
        "intervention": "Emergency safety assessment",
        "description": "Initiate immediate road safety audit at this location. "
                       "Review recent road/construction changes that may contribute to increased accidents. "
                       "Consider temporary speed restrictions pending full audit.",
        "authority": "Bengaluru Traffic Police / BBMP",
        "evidence_basis": "Year-on-year increase in accident frequency signals emerging risk"
    }
}


class RecommendationAgent:
    """
    Agent 4: Road Safety Recommendation Agent.
    Generates evidence-based recommendations from validated analytical outputs.
    All recommendations are linked to specific supporting observations.
    Recommendations are advisory — not verified engineering assessments.
    """

    name = "Road Safety Recommendation Agent"
    agent_id = "recommendation"

    def analyze(self, db: Session, police_station: Optional[str] = None,
                granite_client=None) -> dict:
        start_time = time.time()
        log = AgentExecutionLog(
            agent_name=self.name,
            task_description=f"Recommendation generation for station={police_station}",
            input_params=json.dumps({"police_station": police_station}),
            status="running"
        )
        db.add(log)
        db.flush()

        try:
            result = self._run_analysis(db, police_station, granite_client)
            log.status = "completed"
            log.output_summary = json.dumps({"recommendations": len(result.get("recommendations", []))})
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
                      granite_client) -> dict:
        recommendations = []
        priority_rank = 1

        # Get risk assessments
        ra_query = db.query(RiskAssessment)
        if police_station:
            ra_query = ra_query.filter(RiskAssessment.police_station == police_station)
        ra_list = ra_query.order_by(desc(RiskAssessment.risk_score)).limit(10).all()

        for ra in ra_list:
            station_recs = []

            # Recommendation based on risk tier
            if ra.risk_tier == "HIGH":
                intervention = INTERVENTION_KB["HIGH_FATAL_RATE"]
                station_recs.append(self._make_rec(
                    ra.police_station, priority_rank, "High Fatal Rate Intervention",
                    intervention, f"Risk score {ra.risk_score}/100 (HIGH tier). "
                    f"Fatal accidents: {ra.latest_year_fatal}. YoY change: {ra.yoy_change_pct:+.1f}%",
                    "STRONG"
                ))
                priority_rank += 1

            if ra.risk_tier in ("HIGH", "MEDIUM_HIGH"):
                intervention = INTERVENTION_KB["HIGH_TOTAL_ACCIDENTS"]
                station_recs.append(self._make_rec(
                    ra.police_station, priority_rank, "High Accident Concentration",
                    intervention, f"Total accidents: {ra.latest_year_total} ({ra.risk_tier} tier)",
                    "STRONG"
                ))
                priority_rank += 1

            # Official blackspot recommendations
            bs_list = db.query(OfficialBlackspot).filter(
                OfficialBlackspot.police_station == ra.police_station
            ).all()

            for bs in bs_list:
                lt = (bs.location_type or "").lower()
                if "flyover" in lt or "ramp" in lt:
                    kb_key = "FLYOVER_RAMP"
                elif "bus stop" in lt:
                    kb_key = "BUS_STOP"
                elif "school" in lt or "educational" in lt:
                    kb_key = "SCHOOL_ZONE"
                elif "bridge" in lt:
                    kb_key = "BRIDGE"
                elif "metro" in lt:
                    kb_key = "BUS_STOP"
                else:
                    kb_key = "JUNCTION"

                intervention = INTERVENTION_KB[kb_key]
                station_recs.append(self._make_rec(
                    ra.police_station, priority_rank,
                    f"Official BTP Blackspot: {bs.normalized_location_name}",
                    intervention,
                    f"Official Bengaluru Traffic Police blackspot. Location: {bs.original_location_description}. "
                    f"Type: {bs.location_type}. Road: {bs.road_name}.",
                    "STRONG"
                ))
                priority_rank += 1

            # YoY increase recommendation
            if ra.yoy_change_pct and ra.yoy_change_pct > 15:
                intervention = INTERVENTION_KB["YOY_INCREASE"]
                station_recs.append(self._make_rec(
                    ra.police_station, priority_rank, "Year-on-Year Accident Increase",
                    intervention,
                    f"Accidents increased {ra.yoy_change_pct:+.1f}% year-on-year. Requires immediate investigation.",
                    "MODERATE"
                ))
                priority_rank += 1

            recommendations.extend(station_recs)

        # CAS overspeed recommendations for top wards
        top_overspeed = db.query(CasAlertAggregated).filter(
            CasAlertAggregated.alarm_type == "Overspeed",
            CasAlertAggregated.overspeed_count > 50
        ).order_by(desc(CasAlertAggregated.overspeed_count)).limit(5).all()

        for ward_data in top_overspeed:
            intervention = INTERVENTION_KB["OVERSPEED_ALERTS"]
            rec = self._make_rec(
                f"Ward: {ward_data.ward_name}", priority_rank,
                "High Overspeed Alert Concentration",
                intervention,
                f"Ward {ward_data.ward_name}: {ward_data.overspeed_count} overspeed CAS alerts recorded. "
                f"Note: CAS alerts are driving-safety indicators, not confirmed accidents.",
                "INDICATIVE"
            )
            recommendations.append(rec)
            priority_rank += 1

        # Persist recommendations
        if not police_station:
            db.query(SafetyRecommendation).delete()
        for rec in recommendations:
            sr = SafetyRecommendation(
                police_station=rec["police_station"],
                priority_rank=rec["priority_rank"],
                recommendation_type=rec["recommendation_type"],
                recommendation_text=rec["recommendation_text"],
                evidence_summary=rec["evidence_summary"],
                responsible_authority=rec["responsible_authority"],
                evidence_strength=rec["evidence_strength"],
                data_limitations=rec["data_limitations"],
                generated_by="recommendation_agent",
                granite_enhanced=False
            )
            db.add(sr)
        db.flush()

        return {
            "agent": self.name,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations[:50],  # Cap display at 50
            "disclaimer": (
                "These recommendations are evidence-based suggestions generated from available data. "
                "They are advisory and not verified engineering assessments. "
                "Implementation requires review and approval by qualified traffic engineering authorities."
            )
        }

    def _make_rec(self, station: str, rank: int, rec_type: str, intervention: dict,
                  evidence: str, strength: str) -> dict:
        return {
            "police_station": station,
            "priority_rank": rank,
            "recommendation_type": rec_type,
            "recommendation_text": intervention["intervention"] + ". " + intervention["description"],
            "evidence_summary": evidence,
            "responsible_authority": intervention["authority"],
            "evidence_strength": strength,
            "evidence_basis": intervention["evidence_basis"],
            "data_limitations": (
                "Recommendations based on accident frequency statistics and official BTP blackspot designations. "
                "Road condition, pedestrian count, and traffic volume data not available. "
                "Local field assessment required before implementation."
            )
        }
