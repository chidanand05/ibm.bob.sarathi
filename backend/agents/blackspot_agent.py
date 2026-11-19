"""
ParallaX | Agent 2 — Blackspot Identification Agent
Manages and analyzes official BTP blackspots and high-accident station areas.
Two distinct categories maintained: official BTP blackspots vs data-derived rankings.
"""
import json
import time
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database.models import (
    OfficialBlackspot, AccidentStatistic, RiskAssessment,
    AgentExecutionLog, CasAlertAggregated
)

logger = logging.getLogger(__name__)


class BlackspotAgent:
    """
    Agent 2: Blackspot Identification Agent.
    
    IMPORTANT DISTINCTION:
    - Category 1: Official BTP Blackspots — 64 locations officially designated by Bengaluru Traffic Police
    - Category 2: Data-Derived High-Accident Areas — stations ranked by accident statistics
    
    These are NOT interchangeable. Data-derived rankings are NOT officially identified blackspots.
    """

    name = "Blackspot Identification Agent"
    agent_id = "blackspot"

    def analyze(self, db: Session, police_station: Optional[str] = None,
                blackspot_id: Optional[str] = None) -> dict:
        start_time = time.time()
        log = AgentExecutionLog(
            agent_name=self.name,
            task_description=f"Blackspot analysis for station={police_station}, id={blackspot_id}",
            input_params=json.dumps({"police_station": police_station, "blackspot_id": blackspot_id}),
            status="running"
        )
        db.add(log)
        db.flush()

        try:
            result = self._run_analysis(db, police_station, blackspot_id)
            log.status = "completed"
            log.output_summary = json.dumps({
                "official_blackspots": len(result.get("official_blackspots", [])),
                "high_accident_stations": len(result.get("high_accident_stations", []))
            })
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
                      blackspot_id: Optional[str]) -> dict:
        # Official BTP blackspots
        official_query = db.query(OfficialBlackspot)
        if police_station:
            official_query = official_query.filter(
                OfficialBlackspot.police_station == police_station
            )
        if blackspot_id:
            official_query = official_query.filter(
                OfficialBlackspot.blackspot_id == blackspot_id
            )
        official_bs = official_query.all()

        official_list = []
        for bs in official_bs:
            # Get accident stats for the police station
            station_stats = self._get_station_summary_stats(db, bs.police_station)
            official_list.append({
                "blackspot_id": bs.blackspot_id,
                "police_station": bs.police_station,
                "original_location_description": bs.original_location_description,
                "normalized_location_name": bs.normalized_location_name,
                "road_name": bs.road_name,
                "location_type": bs.location_type,
                "source": bs.source,
                "identification_year": bs.identification_year,
                "latitude": bs.latitude,
                "longitude": bs.longitude,
                "geocoding_status": bs.geocoding_status,
                "verification_status": bs.verification_status,
                "station_accident_context": station_stats,
                "category": "OFFICIAL_BTP_BLACKSPOT"
            })

        # Group by station
        station_groups = {}
        for bs in official_list:
            ps = bs["police_station"]
            if ps not in station_groups:
                station_groups[ps] = []
            station_groups[ps].append(bs)

        # Data-derived high-accident areas (explicitly NOT official blackspots)
        latest_year = db.query(func.max(AccidentStatistic.year)).filter(
            AccidentStatistic.is_summary_row == False
        ).scalar() or 2024

        high_accident_query = db.query(AccidentStatistic).filter(
            AccidentStatistic.year == latest_year,
            AccidentStatistic.is_summary_row == False
        ).order_by(desc(AccidentStatistic.fatal_accidents))

        if police_station:
            high_accident_query = high_accident_query.filter(
                AccidentStatistic.police_station == police_station
            )

        high_accident_stations = []
        for stat in high_accident_query.limit(20).all():
            official_count = db.query(OfficialBlackspot).filter(
                OfficialBlackspot.police_station == stat.police_station
            ).count()
            high_accident_stations.append({
                "police_station": stat.police_station,
                "zone": stat.zone or "Unknown",
                "year": latest_year,
                "fatal_accidents": stat.fatal_accidents or 0,
                "non_fatal_accidents": stat.non_fatal_accidents or 0,
                "total_accidents": stat.total_accidents or 0,
                "people_killed": stat.people_killed or 0,
                "official_blackspot_count": official_count,
                "category": "DATA_DERIVED_HIGH_ACCIDENT_AREA",
                "category_note": "Ranked by accident frequency from police station statistics. "
                                 "NOT an officially designated blackspot."
            })

        return {
            "agent": self.name,
            "analysis_year": latest_year,
            "total_official_blackspots": db.query(OfficialBlackspot).count(),
            "geocoded_blackspots": db.query(OfficialBlackspot).filter(
                OfficialBlackspot.geocoding_status == "geocoded"
            ).count(),
            "stations_with_official_blackspots": len(station_groups),
            "official_blackspots": official_list,
            "station_groups": {
                ps: {
                    "blackspot_count": len(bsl),
                    "blackspots": bsl
                }
                for ps, bsl in station_groups.items()
            },
            "high_accident_stations": high_accident_stations,
            "important_distinction": (
                "Official BTP Blackspots are locations officially designated by Bengaluru Traffic Police. "
                "Data-derived high-accident areas are ranked by accident statistics only. "
                "These are distinct categories and must not be conflated."
            )
        }

    def _get_station_summary_stats(self, db: Session, station: str) -> dict:
        latest_year = db.query(func.max(AccidentStatistic.year)).filter(
            AccidentStatistic.is_summary_row == False
        ).scalar() or 2024
        stat = db.query(AccidentStatistic).filter(
            AccidentStatistic.police_station == station,
            AccidentStatistic.year == latest_year,
            AccidentStatistic.is_summary_row == False
        ).first()
        if stat:
            return {
                "year": latest_year,
                "total_accidents": stat.total_accidents or 0,
                "fatal_accidents": stat.fatal_accidents or 0,
                "non_fatal_accidents": stat.non_fatal_accidents or 0,
            }
        return {}

    def get_all_blackspots(self, db: Session) -> list:
        bss = db.query(OfficialBlackspot).order_by(OfficialBlackspot.police_station).all()
        return [
            {
                "blackspot_id": bs.blackspot_id,
                "police_station": bs.police_station,
                "original_location_description": bs.original_location_description,
                "normalized_location_name": bs.normalized_location_name,
                "road_name": bs.road_name,
                "location_type": bs.location_type,
                "source": bs.source,
                "identification_year": bs.identification_year,
                "latitude": bs.latitude,
                "longitude": bs.longitude,
                "geocoding_status": bs.geocoding_status,
                "verification_status": bs.verification_status,
            }
            for bs in bss
        ]

    def get_map_markers(self, db: Session) -> list:
        """Returns geocoded blackspots for map rendering."""
        bss = db.query(OfficialBlackspot).filter(
            OfficialBlackspot.geocoding_status == "geocoded",
            OfficialBlackspot.latitude.isnot(None),
            OfficialBlackspot.longitude.isnot(None)
        ).all()
        return [
            {
                "blackspot_id": bs.blackspot_id,
                "police_station": bs.police_station,
                "original_location_description": bs.original_location_description,
                "normalized_location_name": bs.normalized_location_name,
                "road_name": bs.road_name,
                "location_type": bs.location_type,
                "source": bs.source,
                "identification_year": bs.identification_year,
                "lat": bs.latitude,
                "lng": bs.longitude,
                "geocoding_status": bs.geocoding_status,
            }
            for bs in bss
        ]
