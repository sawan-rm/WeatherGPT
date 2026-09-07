"""
IMD (India Meteorological Department) Data Service.
Fetches real-time and historical rainfall data from IMD APIs and OpenWeatherMap.
Stores data in the RainfallData table for use by the ML risk engine.
"""
import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.models.rainfall_data import RainfallData

logger = logging.getLogger(__name__)

# NER (North Eastern Region) districts and their approximate coordinates
NER_STATIONS = {
    # Assam
    "Guwahati": {"lat": 26.1445, "lng": 91.7362, "district": "Kamrup Metropolitan", "state": "Assam"},
    "Silchar": {"lat": 24.8333, "lng": 92.7789, "district": "Cachar", "state": "Assam"},
    "Dibrugarh": {"lat": 27.4728, "lng": 94.9120, "district": "Dibrugarh", "state": "Assam"},
    "Jorhat": {"lat": 26.7509, "lng": 94.2037, "district": "Jorhat", "state": "Assam"},
    "Tezpur": {"lat": 26.6338, "lng": 92.8, "district": "Sonitpur", "state": "Assam"},
    "Haflong": {"lat": 25.1648, "lng": 93.0170, "district": "Dima Hasao", "state": "Assam"},

    # Meghalaya
    "Shillong": {"lat": 25.5788, "lng": 91.8933, "district": "East Khasi Hills", "state": "Meghalaya"},
    "Cherrapunji": {"lat": 25.2700, "lng": 91.7200, "district": "East Khasi Hills", "state": "Meghalaya"},
    "Tura": {"lat": 25.5142, "lng": 90.2168, "district": "West Garo Hills", "state": "Meghalaya"},

    # Mizoram
    "Aizawl": {"lat": 23.7271, "lng": 92.7176, "district": "Aizawl", "state": "Mizoram"},
    "Lunglei": {"lat": 22.8867, "lng": 92.7272, "district": "Lunglei", "state": "Mizoram"},

    # Nagaland
    "Kohima": {"lat": 25.6751, "lng": 94.1086, "district": "Kohima", "state": "Nagaland"},
    "Dimapur": {"lat": 25.9042, "lng": 93.7266, "district": "Dimapur", "state": "Nagaland"},

    # Manipur
    "Imphal": {"lat": 24.8170, "lng": 93.9368, "district": "Imphal West", "state": "Manipur"},
    "Churachandpur": {"lat": 24.3337, "lng": 93.6832, "district": "Churachandpur", "state": "Manipur"},

    # Tripura
    "Agartala": {"lat": 23.8315, "lng": 91.2868, "district": "West Tripura", "state": "Tripura"},

    # Sikkim
    "Gangtok": {"lat": 27.3389, "lng": 88.6065, "district": "East Sikkim", "state": "Sikkim"},

    # Arunachal Pradesh
    "Itanagar": {"lat": 27.0844, "lng": 93.6053, "district": "Papum Pare", "state": "Arunachal Pradesh"},
    "Tawang": {"lat": 27.5860, "lng": 91.8600, "district": "Tawang", "state": "Arunachal Pradesh"},
    "Pasighat": {"lat": 28.0700, "lng": 95.3300, "district": "East Siang", "state": "Arunachal Pradesh"},
}


def classify_rainfall_intensity(rainfall_mm: float) -> str:
    """Classify rainfall intensity per IMD standards (in mm/24h)."""
    if rainfall_mm < 7.5:
        return "light"
    elif rainfall_mm < 35.5:
        return "moderate"
    elif rainfall_mm < 64.5:
        return "heavy"
    elif rainfall_mm < 124.5:
        return "very_heavy"
    else:
        return "extremely_heavy"


async def fetch_openweather_rainfall(station_name: str, lat: float, lng: float) -> Optional[dict]:
    """
    Fetch current weather data from OpenWeatherMap API.
    Returns rainfall and temperature data.
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY not set, skipping weather fetch")
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lng,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Extract rainfall (OpenWeatherMap puts it in "rain" key)
        rain_1h = data.get("rain", {}).get("1h", 0.0)
        rain_3h = data.get("rain", {}).get("3h", 0.0)
        temp = data.get("main", {}).get("temp")
        humidity = data.get("main", {}).get("humidity")

        return {
            "rainfall_mm": rain_1h if rain_1h > 0 else rain_3h / 3.0,
            "temperature_c": temp,
            "humidity_pct": humidity,
            "duration_hours": 1.0,
        }

    except httpx.HTTPError as e:
        logger.error(f"OpenWeatherMap API error for {station_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching weather for {station_name}: {e}")
        return None


async def calculate_cumulative_rainfall(
    db: AsyncSession, station_name: str, current_time: datetime
) -> dict:
    """
    Calculate cumulative rainfall for various time windows.
    This is critical for landslide risk assessment — 72h cumulative is the most important.
    """
    cumulative = {}

    for hours, key in [(24, "cumulative_24h"), (48, "cumulative_48h"),
                       (72, "cumulative_72h"), (168, "cumulative_7d")]:
        cutoff = current_time - timedelta(hours=hours)
        result = await db.execute(
            select(func.coalesce(func.sum(RainfallData.rainfall_mm), 0.0))
            .where(RainfallData.station_name == station_name)
            .where(RainfallData.recorded_at >= cutoff)
        )
        cumulative[key] = float(result.scalar())

    return cumulative


async def calculate_antecedent_rainfall_index(
    db: AsyncSession, station_name: str, current_time: datetime, days: int = 5, k: float = 0.85
) -> float:
    """
    Calculate Antecedent Rainfall Index (ARI).
    ARI = sum(rainfall_day_i * k^i) for i = 1 to N days.
    k = decay constant (typically 0.85 for NER soil conditions).
    Higher ARI means soil is already saturated → higher landslide risk.
    """
    ari = 0.0
    for day in range(1, days + 1):
        day_start = current_time - timedelta(days=day)
        day_end = current_time - timedelta(days=day - 1)

        result = await db.execute(
            select(func.coalesce(func.sum(RainfallData.rainfall_mm), 0.0))
            .where(RainfallData.station_name == station_name)
            .where(RainfallData.recorded_at >= day_start)
            .where(RainfallData.recorded_at < day_end)
        )
        daily_rainfall = float(result.scalar())
        ari += daily_rainfall * (k ** day)

    return round(ari, 2)


async def ingest_rainfall_for_all_stations(db: AsyncSession) -> dict:
    """
    Main ingestion function — called by the scheduler every 15 minutes.
    Fetches rainfall data for all NER stations and stores in database.
    Returns summary of ingested data.
    """
    now = datetime.now(timezone.utc)
    ingested = 0
    errors = 0
    high_rainfall_alerts = []

    for station_name, info in NER_STATIONS.items():
        try:
            weather = await fetch_openweather_rainfall(
                station_name, info["lat"], info["lng"]
            )

            if weather is None:
                errors += 1
                continue

            # Calculate cumulative rainfall
            cumulative = await calculate_cumulative_rainfall(db, station_name, now)

            # Calculate ARI
            ari = await calculate_antecedent_rainfall_index(db, station_name, now)

            # Classify intensity
            intensity = classify_rainfall_intensity(weather["rainfall_mm"])

            # Create rainfall record
            rainfall_record = RainfallData(
                station_name=station_name,
                district=info["district"],
                state=info["state"],
                rainfall_mm=weather["rainfall_mm"],
                duration_hours=weather["duration_hours"],
                intensity=intensity,
                cumulative_24h=cumulative["cumulative_24h"] + weather["rainfall_mm"],
                cumulative_48h=cumulative["cumulative_48h"] + weather["rainfall_mm"],
                cumulative_72h=cumulative["cumulative_72h"] + weather["rainfall_mm"],
                cumulative_7d=cumulative["cumulative_7d"] + weather["rainfall_mm"],
                antecedent_rainfall_index=ari,
                temperature_c=weather.get("temperature_c"),
                humidity_pct=weather.get("humidity_pct"),
                source="OpenWeatherMap",
                recorded_at=now,
            )

            db.add(rainfall_record)
            ingested += 1

            # Flag if heavy rainfall detected (critical for alerting)
            if intensity in ("heavy", "very_heavy", "extremely_heavy"):
                high_rainfall_alerts.append({
                    "station": station_name,
                    "district": info["district"],
                    "state": info["state"],
                    "rainfall_mm": weather["rainfall_mm"],
                    "intensity": intensity,
                    "cumulative_72h": cumulative["cumulative_72h"] + weather["rainfall_mm"],
                })

        except Exception as e:
            logger.error(f"Failed to ingest rainfall for {station_name}: {e}")
            errors += 1

    await db.commit()

    summary = {
        "timestamp": now.isoformat(),
        "stations_ingested": ingested,
        "stations_errored": errors,
        "total_stations": len(NER_STATIONS),
        "high_rainfall_alerts": high_rainfall_alerts,
    }

    if high_rainfall_alerts:
        logger.warning(
            f"⚠️ HIGH RAINFALL DETECTED at {len(high_rainfall_alerts)} stations: "
            f"{[a['station'] for a in high_rainfall_alerts]}"
        )

    logger.info(f"✅ Rainfall ingestion complete: {ingested}/{len(NER_STATIONS)} stations")
    return summary
