"""
RiskAssessment model — stores the output of ML risk prediction for each zone.
Each record represents a single assessment at a point in time, forming a time series
of risk predictions that can be visualized as trends.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # Which zone this assessment is for
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=False, index=True)

    # Risk score — continuous value from the ML model
    risk_score = Column(Float, nullable=False)  # 0.0 (safe) to 1.0 (imminent danger)

    # Discretized risk level for alerting and visualization
    risk_level = Column(
        String(20), nullable=False, index=True
    )  # low | medium | high | critical

    # Contributing factor weights — explains WHY this score was given
    contributing_factors = Column(JSONB, nullable=False)
    # Example: {
    #   "rainfall_risk": 0.85,       — 72h cumulative rainfall very high
    #   "soil_saturation": 0.72,     — soil moisture near saturation
    #   "slope_risk": 0.60,          — steep slope in zone
    #   "historical_risk": 0.45,     — past events in this area
    #   "vegetation_risk": 0.30,     — moderate deforestation
    #   "citizen_report_factor": 0.2 — recent citizen reports in zone
    # }

    # Prediction window — how far into the future this assessment covers
    prediction_window_hours = Column(Integer, default=24)  # 6, 12, 24, 48 hours

    # Model confidence (0.0 to 1.0)
    confidence = Column(Float, nullable=True)

    # Which model version produced this assessment (for tracking model improvements)
    model_version = Column(String(50), nullable=True)  # e.g., "xgboost-v1.2", "lstm-v0.3"

    # Change detection — did the risk level change from the previous assessment?
    previous_risk_level = Column(String(20), nullable=True)
    level_changed = Column(Integer, default=0)  # 0=no change, 1=escalated, -1=de-escalated

    # Whether this assessment triggered an alert
    alert_triggered = Column(Integer, default=0)  # 0=no, 1=yes

    # Timestamps
    assessed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<RiskAssessment zone={self.zone_id}: {self.risk_level} ({self.risk_score:.2f})>"
