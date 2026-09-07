"""Pydantic schemas for Infrastructure (Roads, Villages, CriticalInfrastructure) API."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- Road schemas ---

class RoadBase(BaseModel):
    name: str
    road_type: str  # national_highway | state_highway | district_road | village_road | pmgsy
    state: str
    district: Optional[str] = None
    start_point: Optional[str] = None
    end_point: Optional[str] = None
    length_km: Optional[float] = None


class RoadCreate(RoadBase):
    pass


class RoadStatusUpdate(BaseModel):
    status: str  # open | partially_blocked | blocked | damaged | under_repair
    blockage_description: Optional[str] = None
    estimated_clearance_hours: Optional[float] = None
    alternate_route: Optional[str] = None


class RoadResponse(RoadBase):
    id: int
    status: str
    blockage_description: Optional[str] = None
    estimated_clearance_hours: Optional[float] = None
    alternate_route: Optional[str] = None
    last_status_update: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Village schemas ---

class VillageBase(BaseModel):
    name: str
    name_local: Optional[str] = None
    village_code: Optional[str] = None
    district: str
    state: str
    block: Optional[str] = None
    panchayat: Optional[str] = None
    population: Optional[int] = None
    households: Optional[int] = None


class VillageCreate(VillageBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearest_road_id: Optional[int] = None
    distance_to_road_km: Optional[float] = None


class VillageResponse(VillageBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearest_road_id: Optional[int] = None
    distance_to_road_km: Optional[float] = None
    nearest_hospital_km: Optional[float] = None
    accessibility_status: str
    vulnerable: bool
    risk_exposure: str
    has_shelter: bool
    has_mobile_network: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- CriticalInfrastructure schemas ---

class InfraBase(BaseModel):
    name: str
    infra_type: str  # bridge | hospital | school | power_station | dam | water_supply | telecom_tower
    district: str
    state: str
    address: Optional[str] = None


class InfraCreate(InfraBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_id: Optional[int] = None
    capacity: Optional[str] = None
    priority: int = 5


class InfraResponse(InfraBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_id: Optional[int] = None
    risk_exposure_level: str
    status: str
    capacity: Optional[str] = None
    priority: int
    last_inspected_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
