"""
User model — extended with role-based access control for disaster management.
Roles: citizen, field_official, district_admin, state_authority, super_admin
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String(20), nullable=True, index=True)  # For SMS alerts

    # Role-based access
    role = Column(
        String(30), nullable=False, default="citizen", index=True
    )  # citizen | field_official | district_admin | state_authority | super_admin

    # Language & preferences
    preferred_language = Column(String(10), default="en")  # en, hi, as, mz, mn, nag, kha
    sms_alerts_enabled = Column(Boolean, default=True)
    push_alerts_enabled = Column(Boolean, default=True)

    # Location & jurisdiction
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location = Column(Geometry("POINT", srid=4326), nullable=True)  # PostGIS point for geo-queries
    district = Column(String(100), nullable=True, index=True)       # Jurisdiction district
    state = Column(String(100), nullable=True, index=True)          # Jurisdiction state

    # Legacy fields (kept for backward compatibility with WeatherGPT features)
    user_type = Column(String(30), default="general")  # "general" or "farmer"
    crop_types = Column(ARRAY(String), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email/phone verified

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
