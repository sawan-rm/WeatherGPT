from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    name_hi = Column(String, nullable=True) # Hindi name
    season = Column(String, nullable=False) # e.g., Kharif, Rabi, Zaid
    ideal_temp_min = Column(Float, nullable=True)
    ideal_temp_max = Column(Float, nullable=True)
    ideal_rainfall_mm = Column(Float, nullable=True)
    growth_stages_json = Column(JSONB, nullable=True)

class CropAdvisory(Base):
    __tablename__ = "crop_advisories"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    stage = Column(String, nullable=False) # e.g., Sowing, Vegetative, Harvesting
    weather_condition = Column(String, nullable=False) # e.g., heavy_rain, heat_wave
    advisory_text = Column(String, nullable=False)
    advisory_text_hi = Column(String, nullable=True)
