"""
LandslideZone model — represents a geographic area being monitored for landslide risk.
Each zone is a polygon (or point) in PostGIS with terrain, soil, and risk metadata.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class LandslideZone(Base):
    __tablename__ = "landslide_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    zone_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "NER-AS-KAM-001"

    # Administrative
    state = Column(String(100), nullable=False, index=True)   # NER state (Assam, Meghalaya, etc.)
    district = Column(String(100), nullable=False, index=True)
    sub_district = Column(String(100), nullable=True)

    # PostGIS Geometry — store zone boundary as polygon, or centroid as point
    # SRID 4326 = WGS84 (standard lat/lng coordinate system)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=True)
    centroid = Column(Geometry("POINT", srid=4326), nullable=True)

    # Terrain characteristics (from DEM data)
    elevation_m = Column(Float, nullable=True)          # Average elevation in meters
    slope_degree = Column(Float, nullable=True)          # Average slope angle in degrees
    aspect = Column(Float, nullable=True)                # Slope direction (0-360°)
    curvature = Column(Float, nullable=True)             # Profile curvature
    relief = Column(Float, nullable=True)                # Relative relief in meters

    # Soil & land characteristics
    soil_type = Column(String(100), nullable=True)       # e.g., "laterite", "alluvial", "clay"
    vegetation_cover = Column(String(50), nullable=True) # e.g., "dense_forest", "sparse", "barren"
    land_use = Column(String(100), nullable=True)        # e.g., "settlement", "agriculture", "forest"
    lithology = Column(String(100), nullable=True)       # Rock type underneath

    # Baseline risk (from geological survey + terrain analysis)
    risk_baseline = Column(
        String(20), nullable=False, default="medium"
    )  # low / medium / high / critical

    # Monitoring status
    is_active = Column(Boolean, default=True, nullable=False)
    has_sensors = Column(Boolean, default=False)         # Whether IoT sensors are installed
    monitoring_priority = Column(Integer, default=5)     # 1 (highest) to 10 (lowest)

    # Descriptive
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    last_assessed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LandslideZone {self.zone_code}: {self.name} ({self.state})>"
