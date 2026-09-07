"""
CitizenReport model — geo-tagged field reports submitted by citizens and field officials.
Supports photo/video uploads, GPS coordinates, and offline-first submission.
These reports feed into the risk model as a human intelligence signal.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Reporter
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Linked zone (auto-determined from GPS or manually selected)
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=True, index=True)

    # Report classification
    report_type = Column(
        String(50), nullable=False, index=True
    )  # crack | slope_movement | road_block | flooding | soil_erosion | unusual_seepage | other

    severity_estimate = Column(
        String(20), nullable=False, default="unknown"
    )  # low | medium | high | critical | unknown

    # Content
    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)

    # Location — PostGIS point from device GPS
    location = Column(Geometry("POINT", srid=4326), nullable=True)
    location_accuracy_m = Column(Float, nullable=True)     # GPS accuracy in meters
    address_text = Column(String(500), nullable=True)      # Reverse-geocoded or manual address

    # Media attachments — URLs to uploaded photos/videos
    media_urls = Column(ARRAY(String), nullable=True)      # ["https://storage/.../photo1.jpg", ...]
    media_metadata = Column(JSONB, nullable=True)
    # Example: [{"type": "image", "exif_lat": 25.6, "exif_lng": 93.2, "taken_at": "..."}]

    # Verification workflow
    status = Column(
        String(30), nullable=False, default="pending", index=True
    )  # pending | under_review | verified | resolved | false_alarm | duplicate

    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_notes = Column(Text, nullable=True)

    # If this report led to a confirmed landslide event
    linked_event_id = Column(
        Integer, ForeignKey("landslide_events.id", use_alter=True), nullable=True
    )

    # Offline sync support
    client_report_id = Column(String(100), nullable=True, unique=True)  # UUID generated client-side
    submitted_offline = Column(Boolean, default=False)

    # Upvotes from other citizens (crowdsourced verification)
    upvote_count = Column(Integer, default=0)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<CitizenReport {self.id}: {self.report_type}/{self.status}>"
