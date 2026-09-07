"""
SensorReading model — stores time-series data from IoT sensors deployed in the field.
Supports soil moisture, rain gauge, tilt/inclinometer, and piezometer sensors.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)

    # Link to monitored zone
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=False, index=True)

    # Sensor identification
    device_id = Column(String(100), nullable=False, index=True)  # Unique sensor device ID
    sensor_type = Column(
        String(50), nullable=False, index=True
    )  # soil_moisture | rain_gauge | tilt | piezometer | temperature

    # Reading data
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)  # e.g., "%", "mm", "degrees", "kPa", "°C"

    # Sensor location (specific point, may differ slightly from zone centroid)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    # Quality & status
    battery_level = Column(Float, nullable=True)       # Battery % (0-100)
    signal_strength = Column(Float, nullable=True)     # RSSI or signal quality
    is_anomaly = Column(Integer, default=0)            # 0=normal, 1=flagged by anomaly detection

    # Timestamps
    reading_at = Column(DateTime(timezone=True), nullable=False, index=True)  # When sensor took the reading
    received_at = Column(DateTime(timezone=True), server_default=func.now())  # When server received it

    def __repr__(self):
        return f"<SensorReading {self.device_id}/{self.sensor_type}: {self.value}{self.unit}>"
