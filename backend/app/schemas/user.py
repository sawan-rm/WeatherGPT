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

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
