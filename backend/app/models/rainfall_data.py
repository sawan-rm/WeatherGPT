"""
RainfallData model — stores IMD and other weather station rainfall observations.
Used as a primary input feature for the ML risk prediction model.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class RainfallData(Base):
    __tablename__ = "rainfall_data"

    id = Column(Integer, primary_key=True, index=True)

    # Link to zone (nullable — some stations might not map directly to a zone)
    zone_id = Column(Integer, ForeignKey("landslide_zones.id"), nullable=True, index=True)

    # Station identification
    station_name = Column(String(200), nullable=False, index=True)
    station_code = Column(String(50), nullable=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)

    # Rainfall measurements
    rainfall_mm = Column(Float, nullable=False)          # Rainfall amount in mm
    duration_hours = Column(Float, nullable=True)         # Duration of measurement period
    intensity = Column(
        String(30), nullable=True
    )  # light (<7.5mm) | moderate (7.5-35.5) | heavy (35.5-64.5) | very_heavy (64.5-124.5) | extremely_heavy (>124.5)

    # Cumulative calculations (critical for landslide prediction)
    cumulative_24h = Column(Float, nullable=True)     # Last 24 hours cumulative rainfall (mm)
    cumulative_48h = Column(Float, nullable=True)     # Last 48 hours
    cumulative_72h = Column(Float, nullable=True)     # Last 72 hours (most used in landslide models)
    cumulative_7d = Column(Float, nullable=True)      # Last 7 days

    # Antecedent Rainfall Index (ARI) — weighted sum of previous days' rainfall
    antecedent_rainfall_index = Column(Float, nullable=True)

    # Temperature (supplementary — affects soil conditions)
    temperature_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)

    # Data source
    source = Column(String(50), default="IMD")  # IMD | OpenWeatherMap | AWS (Auto Weather Station)

    # Timestamps
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)  # Observation time
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())    # When we pulled the data

    def __repr__(self):
        return f"<RainfallData {self.station_name}: {self.rainfall_mm}mm @ {self.recorded_at}>"
