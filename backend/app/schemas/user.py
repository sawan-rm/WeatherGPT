"""Pydantic schemas for User — updated with RBAC role fields."""
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    email: EmailStr
    preferred_language: str = "en"
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    user_type: str = "general"
    crop_types: Optional[List[str]] = None

    # New landslide platform fields
    phone_number: Optional[str] = None
    role: str = "citizen"  # citizen | field_official | district_admin | state_authority | super_admin
    district: Optional[str] = None
    state: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = None
    phone_number: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    district: Optional[str] = None
    state: Optional[str] = None
    sms_alerts_enabled: Optional[bool] = None
    push_alerts_enabled: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True
