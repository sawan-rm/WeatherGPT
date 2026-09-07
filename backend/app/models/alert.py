"""
LandslideAlert model — evolved from the original Alert model.
Represents multi-channel, multi-language alerts issued when risk escalates.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class LandslideAlert(Base):
    __tablename__ = "landslide_alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Which zone triggered this alert
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=False, index=True)

    # Risk assessment that triggered this alert
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessments.id"), nullable=True)

    # Alert classification
    alert_type = Column(
        String(30), nullable=False, index=True
    )  # warning | watch | advisory | all_clear

    risk_level = Column(
        String(20), nullable=False, index=True
    )  # medium | high | critical

    severity = Column(
        String(20), nullable=False, default="moderate"
    )  # minor | moderate | severe | extreme

    # Content — multilingual messages stored as JSONB
    title = Column(String(500), nullable=False)
    message = Column(JSONB, nullable=False)
    # Example: {
    #   "en": "HIGH risk of landslide in Kamrup district. Avoid NH-6 between...",
    #   "hi": "कामरूप जिले में भूस्खलन का उच्च जोखिम...",
    #   "as": "কামৰূপ জিলাত ভূমিস্খলনৰ উচ্চ বিপদ..."
    # }

    # Delivery configuration
    delivery_channels = Column(ARRAY(String), nullable=False)  # ["sms", "push", "dashboard", "email"]
    target_roles = Column(ARRAY(String), nullable=True)  # ["citizen", "field_official", "district_admin"]
    target_district = Column(String(100), nullable=True)
    target_state = Column(String(100), nullable=True)

    # Delivery stats
    recipients_count = Column(Integer, default=0)
    sms_sent_count = Column(Integer, default=0)
    push_sent_count = Column(Integer, default=0)

    # Status & workflow
    status = Column(
        String(20), nullable=False, default="active", index=True
    )  # active | acknowledged | resolved | expired | cancelled

    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalated_to = Column(String(30), nullable=True)  # Role it was escalated to

    # Instructions for recipients
    recommended_actions = Column(Text, nullable=True)
    evacuation_required = Column(Boolean, default=False)

    # Timestamps
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<LandslideAlert {self.id}: {self.alert_type}/{self.risk_level} for zone {self.zone_id}>"


# Keep the old AlertSubscription for backward compatibility but link to zones
class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=True)  # Subscribe to a zone
    location = Column(String, nullable=True)   # Legacy: text-based location
    alert_types = Column(ARRAY(String), nullable=False)
    active = Column(Boolean, default=True)
