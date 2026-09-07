"""Pydantic schemas for RiskAssessment API responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RiskAssessmentResponse(BaseModel):
    id: int
    zone_id: int
    risk_score: float
    risk_level: str
    contributing_factors: dict
    prediction_window_hours: int
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    previous_risk_level: Optional[str] = None
    level_changed: int
    alert_triggered: int
    assessed_at: datetime

    class Config:
        from_attributes = True


class RiskSummaryResponse(BaseModel):
    """Overall risk summary across all zones."""
    total_zones: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    critical_risk_count: int
    active_alerts: int
    blocked_roads: int
    recent_events_24h: int
    last_assessment_at: Optional[datetime] = None


class ZoneRiskTrendResponse(BaseModel):
    """Risk trend for a single zone over time."""
    zone_id: int
    zone_name: str
    assessments: list[RiskAssessmentResponse]
