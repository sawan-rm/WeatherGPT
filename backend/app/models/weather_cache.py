from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True)
    location_key = Column(String, index=True, nullable=False) # e.g., "lat,lng" or "city"
    data_type = Column(String, index=True, nullable=False) # "current" or "forecast"
    response_json = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
