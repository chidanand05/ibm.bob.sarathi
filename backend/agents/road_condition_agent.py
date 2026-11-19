"""
ParallaX | Agent 3 — Road Condition Analysis Agent
IMPORTANT: The supplied datasets contain no road-condition images or surface measurements.
This agent correctly reports unavailable state and provides integration interface.
"""
import json
import time
import logging
from sqlalchemy.orm import Session
from ..database.models import AgentExecutionLog

logger = logging.getLogger(__name__)


class RoadConditionAgent:
    """
    Agent 3: Road Condition Analysis Agent.
    
    Current data availability: NO road-condition images or surface measurement
    data is available in the supplied datasets (5 accident CSVs + 1 CAS alert CSV).
    
    This agent:
    1. Correctly reports that no road-condition source is currently available
    2. Provides structured interface for future data integration
    3. Notes CAS alert overspeeding patterns as the nearest available proxy
    4. Does NOT invent pothole detections or fabricate condition scores
    """

    name = "Road Condition Analysis Agent"
    agent_id = "road_condition"

    def analyze(self, db: Session, police_station: str = None) -> dict:
        start_time = time.time()
        log = AgentExecutionLog(
            agent_name=self.name,
            task_description=f"Road condition analysis for station={police_station}",
            input_params=json.dumps({"police_station": police_station}),
            status="running"
        )
        db.add(log)
        db.flush()

        result = self._run_analysis(db, police_station)
        log.status = "completed"
        log.output_summary = json.dumps({"status": result.get("availability_status")})
        log.execution_time_ms = int((time.time() - start_time) * 1000)
        db.commit()
        return result

    def _run_analysis(self, db: Session, police_station: str = None) -> dict:
        # Fetch overspeed CAS data as nearest available indicator
        from sqlalchemy import func
        from ..database.models import CasAlertAggregated

        overspeed_data = db.query(
            CasAlertAggregated.ward_name,
            func.sum(CasAlertAggregated.overspeed_count).label("overspeed_total"),
            func.sum(CasAlertAggregated.alert_count).label("alert_total"),
            func.max(CasAlertAggregated.max_speed).label("max_speed"),
            func.avg(CasAlertAggregated.avg_speed).label("avg_speed")
        ).filter(
            CasAlertAggregated.alarm_type == "Overspeed"
        ).group_by(CasAlertAggregated.ward_name).order_by(
            func.sum(CasAlertAggregated.overspeed_count).desc()
        ).limit(20).all()

        overspeed_list = [
            {
                "ward": r.ward_name,
                "overspeed_alert_count": int(r.overspeed_total or 0),
                "total_alerts_in_ward": int(r.alert_total or 0),
                "max_recorded_speed": float(r.max_speed or 0),
                "avg_speed": round(float(r.avg_speed or 0), 1),
                "note": "Overspeed alerts are CAS driving-safety indicators, not road-condition measurements"
            }
            for r in overspeed_data
        ]

        return {
            "agent": self.name,
            "availability_status": "ROAD_CONDITION_DATA_UNAVAILABLE",
            "message": (
                "No road-condition images, pothole surveys, or surface measurement data "
                "are available in the current dataset. This agent will provide analysis "
                "when road-condition images or survey data are supplied."
            ),
            "unavailable_capabilities": [
                "Pothole detection (requires road surface images)",
                "Lane marking assessment (requires road images)",
                "Signage condition analysis (requires field survey or images)",
                "Road surface quality scoring (requires sensor or image data)"
            ],
            "available_indicator": {
                "type": "CAS Overspeed Alert Concentration",
                "description": (
                    "Overspeeding CAS alerts may indicate road sections where "
                    "vehicle speeds are elevated, which can be associated with certain "
                    "road conditions (wide roads, poor signage). "
                    "This is an indirect indicator only — not a road-condition measurement."
                ),
                "data": overspeed_list,
                "caveat": "Overspeed alerts represent driving behavior, not road surface quality."
            },
            "future_integration": {
                "supported_formats": ["JPEG/PNG road images", "Pothole survey CSV", "Road inspection GIS data"],
                "integration_endpoint": "POST /api/road-condition/upload-images",
                "cv_model_planned": "YOLOv8 fine-tuned on RDD2022 Indian road damage dataset"
            }
        }

    def get_status(self) -> dict:
        return {
            "agent": self.name,
            "data_available": False,
            "status": "AWAITING_DATA",
            "message": "Road condition analysis requires road surface images or survey data not yet supplied."
        }
