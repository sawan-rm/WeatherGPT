"""Pydantic schemas for LandslideZone API requests/responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ZoneBase(BaseModel):
    name: str
    zone_code: str
    state: str
    district: str
    sub_district: Optional[str] = None
    elevation_m: Optional[float] = None
    slope_degree: Optional[float] = None
    aspect: Optional[float] = None
    curvature: Optional[float] = None
    relief: Optional[float] = None
    soil_type: Optional[str] = None
    vegetation_cover: Optional[str] = None
    land_use: Optional[str] = None
    lithology: Optional[str] = None
    risk_baseline: str = "medium"
    is_active: bool = True
    has_sensors: bool = False
    monitoring_priority: int = 5
    description: Optional[str] = None
    notes: Optional[str] = None


class ZoneCreate(ZoneBase):
    # Lat/lng for centroid (converted to PostGIS POINT server-side)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    risk_baseline: Optional[str] = None
    is_active: Optional[bool] = None
    has_sensors: Optional[bool] = None
    monitoring_priority: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    soil_type: Optional[str] = None
    vegetation_cover: Optional[str] = None
    land_use: Optional[str] = None


class ZoneResponse(ZoneBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_assessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Current risk info (populated from latest RiskAssessment)
    current_risk_score: Optional[float] = None
    current_risk_level: Optional[str] = None

    class Config:
        from_attributes = True


class ZoneListResponse(BaseModel):
    zones: list[ZoneResponse]
    total: int
    page: int
    page_size: int
