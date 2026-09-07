"""
LandslideEvent model — records historical and real-time confirmed landslide events.
Historical data from GSI (Geological Survey of India) feeds the ML training pipeline.
Real-time events are created from verified citizen reports or authority confirmations.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class LandslideEvent(Base):
    __tablename__ = "landslide_events"

    id = Column(Integer, primary_key=True, index=True)

    # Link to zone
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=True, index=True)

    # Event classification
    event_type = Column(
        String(50), nullable=False, index=True
    )  # landslide | rockfall | mudflow | debris_flow | flash_flood | slope_failure | road_collapse

    severity = Column(
        String(20), nullable=False, index=True
    )  # minor | moderate | severe | catastrophic

    # Location
    location = Column(Geometry("POINT", srid=4326), nullable=True)
    location_description = Column(String(500), nullable=True)  # Human-readable location
    district = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True, index=True)

    # Event details
    description = Column(Text, nullable=True)
    cause = Column(String(200), nullable=True)  # heavy_rainfall | earthquake | hill_cutting | road_construction

    # Impact assessment
    casualties = Column(Integer, default=0)
    injuries = Column(Integer, default=0)
    houses_damaged = Column(Integer, default=0)
    infrastructure_damage = Column(Text, nullable=True)  # Free text description of damage
    road_blocked = Column(Boolean, default=False)
    road_name = Column(String(200), nullable=True)
    estimated_clearance_hours = Column(Float, nullable=True)

    # Volume/dimensions (if measured)
    volume_cubic_m = Column(Float, nullable=True)
    length_m = Column(Float, nullable=True)
    width_m = Column(Float, nullable=True)

    # Reporting chain
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Linked citizen report (if event originated from a citizen report)
    source_report_id = Column(Integer, ForeignKey("citizen_reports.id", use_alter=True), nullable=True)

    # Weather conditions at time of event
    weather_conditions = Column(JSONB, nullable=True)
    # Example: {"rainfall_24h_mm": 150, "rainfall_72h_mm": 340, "soil_moisture_pct": 92}

    # Data source
    source = Column(String(50), default="field_report")  # gsi_historical | field_report | satellite | citizen

    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=True, index=True)
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<LandslideEvent {self.id}: {self.event_type}/{self.severity} @ {self.state}>"
