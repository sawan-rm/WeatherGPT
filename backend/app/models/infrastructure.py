"""
Infrastructure models — Roads, Villages, and Critical Infrastructure.
These are core GIS layers used for impact analysis when a landslide risk is predicted.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class Road(Base):
    """Road segments in the NER road network. Used for connectivity analysis."""
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(300), nullable=False, index=True)  # e.g., "NH-6", "Imphal-Kohima Road"
    road_type = Column(
        String(30), nullable=False, index=True
    )  # national_highway | state_highway | district_road | village_road | pmgsy

    # Road geometry — LineString in PostGIS
    geometry = Column(Geometry("LINESTRING", srid=4326), nullable=True)

    # Administrative
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    start_point = Column(String(200), nullable=True)  # From where
    end_point = Column(String(200), nullable=True)     # To where
    length_km = Column(Float, nullable=True)

    # Current status
    status = Column(
        String(30), nullable=False, default="open", index=True
    )  # open | partially_blocked | blocked | damaged | under_repair

    blockage_description = Column(Text, nullable=True)
    estimated_clearance_hours = Column(Float, nullable=True)
    alternate_route = Column(String(500), nullable=True)

    # Risk exposure — which zones does this road pass through?
    # (Handled via spatial query: ST_Intersects(road.geometry, zone.geometry))

    # Timestamps
    last_status_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Road {self.name} ({self.road_type}): {self.status}>"


class Village(Base):
    """Villages in the NER with population and accessibility data."""
    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False, index=True)
    name_local = Column(String(200), nullable=True)  # Name in local language
    village_code = Column(String(50), nullable=True, unique=True)  # Census village code

    # Administrative
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    block = Column(String(100), nullable=True)
    panchayat = Column(String(100), nullable=True)

    # Location
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    # Demographics
    population = Column(Integer, nullable=True)
    households = Column(Integer, nullable=True)

    # Connectivity
    nearest_road_id = Column(Integer, ForeignKey("roads.id"), nullable=True)
    distance_to_road_km = Column(Float, nullable=True)
    nearest_hospital_km = Column(Float, nullable=True)
    nearest_town = Column(String(200), nullable=True)

    # Risk & accessibility
    accessibility_status = Column(
        String(30), default="accessible"
    )  # accessible | limited | isolated | cut_off
    vulnerable = Column(Boolean, default=False)  # Flagged as highly vulnerable
    risk_exposure = Column(String(20), default="low")  # low | medium | high | critical

    # Shelter & resources
    has_shelter = Column(Boolean, default=False)
    shelter_capacity = Column(Integer, nullable=True)
    has_mobile_network = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Village {self.name}, {self.district}, {self.state}>"


class CriticalInfrastructure(Base):
    """Critical infrastructure — bridges, hospitals, schools, power stations, etc."""
    __tablename__ = "critical_infrastructure"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(300), nullable=False, index=True)
    infra_type = Column(
        String(50), nullable=False, index=True
    )  # bridge | hospital | school | power_station | dam | water_supply | telecom_tower | government_office

    # Location
    location = Column(Geometry("POINT", srid=4326), nullable=True)
    address = Column(String(500), nullable=True)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)

    # Link to zone
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=True)

    # Risk exposure
    risk_exposure_level = Column(String(20), default="low")  # low | medium | high | critical
    last_inspected_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(30), default="operational")  # operational | damaged | non_operational
    capacity = Column(String(200), nullable=True)  # e.g., "100 beds" for hospital

    # Importance
    priority = Column(Integer, default=5)  # 1 (most critical) to 10

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CriticalInfrastructure {self.name} ({self.infra_type})>"
