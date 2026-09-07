"""Pydantic schemas for CitizenReport API requests/responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportBase(BaseModel):
    report_type: str  # crack | slope_movement | road_block | flooding | soil_erosion | unusual_seepage | other
    severity_estimate: str = "unknown"
    title: Optional[str] = None
    description: Optional[str] = None


class ReportCreate(ReportBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy_m: Optional[float] = None
    address_text: Optional[str] = None
    zone_id: Optional[int] = None
    media_urls: Optional[list[str]] = None

    # For offline sync
    client_report_id: Optional[str] = None
    submitted_offline: bool = False


class ReportBatchSync(BaseModel):
    """Batch upload queued offline reports."""
    reports: list[ReportCreate]


class ReportUpdate(BaseModel):
    status: Optional[str] = None
    verification_notes: Optional[str] = None
    severity_estimate: Optional[str] = None
    linked_event_id: Optional[int] = None


class ReportResponse(ReportBase):
    id: int
    user_id: int
    zone_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy_m: Optional[float] = None
    address_text: Optional[str] = None
    media_urls: Optional[list[str]] = None
    status: str
    verified_by: Optional[int] = None
    verification_notes: Optional[str] = None
    linked_event_id: Optional[int] = None
    client_report_id: Optional[str] = None
    submitted_offline: bool
    upvote_count: int
    submitted_at: datetime
    verified_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int
    page: int
    page_size: int
