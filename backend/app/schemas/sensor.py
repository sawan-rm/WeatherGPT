"""Pydantic schemas for SensorReading API requests/responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SensorReadingBase(BaseModel):
    zone_id: int
    device_id: str
    sensor_type: str  # soil_moisture | rain_gauge | tilt | piezometer | temperature
    value: float
    unit: str


class SensorReadingCreate(SensorReadingBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    reading_at: datetime


class SensorReadingBatchCreate(BaseModel):
    """For batch upload of multiple sensor readings (offline sync)."""
    readings: list[SensorReadingCreate]


class SensorReadingResponse(SensorReadingBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    is_anomaly: int
    reading_at: datetime
    received_at: datetime

    class Config:
        from_attributes = True


class SensorStatsResponse(BaseModel):
    """Aggregated sensor stats for a zone."""
    zone_id: int
    sensor_type: str
    latest_value: float
    avg_24h: Optional[float] = None
    min_24h: Optional[float] = None
    max_24h: Optional[float] = None
    reading_count_24h: int
    last_reading_at: datetime
