"""
ParallaX | Bengaluru Road Safety & Accident Risk Intelligence Platform
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from .db import Base


class PoliceStation(Base):
    __tablename__ = "police_stations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    normalized_name = Column(String(100), index=True)
    zone = Column(String(50))
    sub_division = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=func.now())


class AccidentStatistic(Base):
    __tablename__ = "accident_statistics"
    id = Column(Integer, primary_key=True, index=True)
    police_station = Column(String(100), index=True)
    zone = Column(String(50))
    year = Column(Integer, index=True)
    fatal_accidents = Column(Integer, default=0)
    non_fatal_accidents = Column(Integer, default=0)
    total_accidents = Column(Integer, default=0)
    people_killed = Column(Integer, default=0)
    people_injured = Column(Integer, default=0)
    source_dataset = Column(String(100))
    is_summary_row = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_station_year", "police_station", "year"),
    )


class HistoricalAccidentStat(Base):
    __tablename__ = "historical_accident_statistics"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, index=True)
    fatal_accidents = Column(Integer, default=0)
    people_killed = Column(Integer, default=0)
    non_fatal_accidents = Column(Integer, default=0)
    people_injured = Column(Integer, default=0)
    total_accidents = Column(Integer, default=0)
    source_dataset = Column(String(100))
    created_at = Column(DateTime, default=func.now())


class OfficialBlackspot(Base):
    __tablename__ = "official_blackspots"
    id = Column(Integer, primary_key=True, index=True)
    blackspot_id = Column(String(10), unique=True, index=True)
    police_station = Column(String(100), index=True)
    original_location_description = Column(Text)
    normalized_location_name = Column(String(200))
    road_name = Column(String(200))
    location_type = Column(String(100))
    source = Column(String(200))
    identification_year = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geocoding_status = Column(String(50), default="pending")
    verification_status = Column(String(50), default="unverified")
    created_at = Column(DateTime, default=func.now())


class CasAlertAggregated(Base):
    __tablename__ = "cas_alerts_aggregated"
    id = Column(Integer, primary_key=True, index=True)
    ward_name = Column(String(100), index=True)
    alarm_type = Column(String(50), index=True)
    alert_count = Column(Integer, default=0)
    avg_speed = Column(Float, default=0)
    max_speed = Column(Float, default=0)
    min_speed = Column(Float, default=0)
    overspeed_count = Column(Integer, default=0)
    unique_devices = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_ward_alarm", "ward_name", "alarm_type"),
    )


class CasAlertSpatial(Base):
    __tablename__ = "cas_alerts_spatial"
    id = Column(Integer, primary_key=True, index=True)
    lat_bin = Column(Float, index=True)
    lng_bin = Column(Float, index=True)
    alert_count = Column(Integer, default=0)
    overspeed_count = Column(Integer, default=0)
    alarm_types_json = Column(Text)
    created_at = Column(DateTime, default=func.now())


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    police_station = Column(String(100), index=True)
    zone = Column(String(50))
    risk_score = Column(Float, default=0)
    risk_tier = Column(String(20))  # HIGH, MEDIUM_HIGH, MODERATE, LOW
    fatal_score_component = Column(Float, default=0)
    total_score_component = Column(Float, default=0)
    blackspot_count = Column(Integer, default=0)
    cas_alert_count = Column(Integer, default=0)
    latest_year_total = Column(Integer, default=0)
    latest_year_fatal = Column(Integer, default=0)
    yoy_change_pct = Column(Float, default=0)
    methodology = Column(Text)
    calculated_at = Column(DateTime, default=func.now())


class SafetyRecommendation(Base):
    __tablename__ = "safety_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    police_station = Column(String(100), index=True)
    priority_rank = Column(Integer)
    recommendation_type = Column(String(100))
    recommendation_text = Column(Text)
    evidence_summary = Column(Text)
    responsible_authority = Column(String(200))
    evidence_strength = Column(String(20))  # STRONG, MODERATE, INDICATIVE
    data_limitations = Column(Text)
    generated_by = Column(String(50), default="recommendation_agent")
    granite_enhanced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), index=True)
    task_description = Column(Text)
    input_params = Column(Text)
    output_summary = Column(Text)
    status = Column(String(20))  # running, completed, failed
    execution_time_ms = Column(Integer)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


class DataSourceMetadata(Base):
    __tablename__ = "data_source_metadata"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), unique=True)
    file_path = Column(String(500))
    record_count = Column(Integer, default=0)
    date_coverage = Column(String(200))
    available_fields = Column(Text)
    validation_status = Column(String(50))
    known_limitations = Column(Text)
    last_processed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())


class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), index=True)
    check_name = Column(String(100))
    check_result = Column(String(20))  # PASS, FAIL, WARNING
    details = Column(Text)
    created_at = Column(DateTime, default=func.now())
