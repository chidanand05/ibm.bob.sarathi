"""
ParallaX | Multi-Agent Orchestrator
Coordinates the five specialized road safety agents.
"""
import logging
from sqlalchemy.orm import Session
from .accident_risk_agent import AccidentRiskAgent
from .blackspot_agent import BlackspotAgent
from .road_condition_agent import RoadConditionAgent
from .recommendation_agent import RecommendationAgent
from .dashboard_agent import DashboardAgent

logger = logging.getLogger(__name__)

class RoadSafetyOrchestrator:
    """
    Orchestrates the 5 agents in a directed workflow:
    Agent1 (risk) → Agent2 (blackspot) → Agent3 (road condition) → Agent4 (recommendations) → Agent5 (dashboard)
    """
    def __init__(self):
        self.risk_agent = AccidentRiskAgent()
        self.blackspot_agent = BlackspotAgent()
        self.road_condition_agent = RoadConditionAgent()
        self.recommendation_agent = RecommendationAgent()
        self.dashboard_agent = DashboardAgent()

    def run_full_analysis(self, db: Session, police_station: str = None,
                          year: int = None, granite_client=None) -> dict:
        results = {}
        errors = {}

        # Agent 1: Risk prediction
        try:
            results["accident_risk"] = self.risk_agent.analyze(db, police_station, year)
        except Exception as e:
            errors["accident_risk"] = str(e)

        # Agent 2: Blackspot identification
        try:
            results["blackspot"] = self.blackspot_agent.analyze(db, police_station)
        except Exception as e:
            errors["blackspot"] = str(e)

        # Agent 3: Road condition (reports unavailable)
        try:
            results["road_condition"] = self.road_condition_agent.analyze(db, police_station)
        except Exception as e:
            errors["road_condition"] = str(e)

        # Agent 4: Recommendations (depends on 1+2+3)
        try:
            results["recommendations"] = self.recommendation_agent.analyze(db, police_station, granite_client)
        except Exception as e:
            errors["recommendations"] = str(e)

        # Agent 5: Dashboard coordination
        try:
            results["dashboard"] = self.dashboard_agent.analyze(db)
        except Exception as e:
            errors["dashboard"] = str(e)

        return {
            "orchestration": "complete",
            "agents_executed": list(results.keys()),
            "agents_failed": list(errors.keys()),
            "errors": errors,
            "results": results
        }

    def run_station_analysis(self, db: Session, police_station: str, granite_client=None) -> dict:
        return self.run_full_analysis(db, police_station=police_station, granite_client=granite_client)
