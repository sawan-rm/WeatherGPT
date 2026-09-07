"""Pydantic schemas for RainfallData API requests/responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RainfallDataBase(BaseModel):
    station_name: str
    station_code: Optional[str] = None
    district: str
    state: str
    rainfall_mm: float
    duration_hours: Optional[float] = None
    intensity: Optional[str] = None
    source: str = "IMD"


class RainfallDataCreate(RainfallDataBase):
    zone_id: Optional[int] = None
    cumulative_24h: Optional[float] = None
    cumulative_48h: Optional[float] = None
    cumulative_72h: Optional[float] = None
    cumulative_7d: Optional[float] = None
    antecedent_rainfall_index: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    recorded_at: datetime


class RainfallDataResponse(RainfallDataBase):
    id: int
    zone_id: Optional[int] = None
    cumulative_24h: Optional[float] = None
    cumulative_48h: Optional[float] = None
    cumulative_72h: Optional[float] = None
    cumulative_7d: Optional[float] = None
    antecedent_rainfall_index: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    recorded_at: datetime
    fetched_at: datetime

    class Config:
        from_attributes = True


class RainfallSummaryResponse(BaseModel):
    """Rainfall summary for a district or zone."""
    district: str
    state: str
    current_rainfall_mm: float
    cumulative_24h: float
    cumulative_72h: float
    intensity: str
    risk_indicator: str  # normal | elevated | high | critical
    last_updated: datetime
