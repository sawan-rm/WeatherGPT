from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    preferred_language = Column(String, default="en")
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    user_type = Column(String, default="general") # "general" or "farmer"
    crop_types = Column(ARRAY(String), nullable=True) # Array of crop names for farmers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
