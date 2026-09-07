"""
IoT Sensor Ingestion Service.
Handles ingestion of data from field-deployed sensors (soil moisture, rain gauges,
tilt/inclinometers, piezometers) via HTTP API endpoints.

For a personal project, we use HTTP-based push (sensors POST to our API).
In production, this would use MQTT broker for low-power, low-bandwidth IoT devices.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

# Anomaly detection thresholds per sensor type
ANOMALY_THRESHOLDS = {
    "soil_moisture": {
        "min": 0.0,    # % volumetric water content
        "max": 100.0,
        "spike_pct": 30.0,   # % change in 1 hour = anomaly
        "critical_high": 85.0,  # Above 85% = near saturation = landslide risk
    },
    "rain_gauge": {
        "min": 0.0,
        "max": 500.0,   # mm — max plausible in 1 reading period
        "spike_pct": None,
        "critical_high": 50.0,  # >50mm in single reading = heavy rain event
    },
    "tilt": {
        "min": -90.0,   # degrees
        "max": 90.0,
        "spike_pct": 5.0,    # 5% change in tilt = potential slope movement!
        "critical_high": 15.0,  # >15° tilt = critical alert
    },
    "piezometer": {
        "min": 0.0,     # kPa
        "max": 1000.0,
        "spike_pct": 25.0,
        "critical_high": 500.0,
    },
    "temperature": {
        "min": -20.0,
        "max": 60.0,
        "spike_pct": None,
        "critical_high": None,
    },
}


async def check_reading_anomaly(
    db: AsyncSession,
    zone_id: int,
    device_id: str,
    sensor_type: str,
    new_value: float,
    reading_at: datetime,
) -> bool:
    """
    Check if a new sensor reading is anomalous.
    
    Anomaly detection rules:
    1. Value out of plausible range
    2. Sudden spike compared to recent readings
    3. Value exceeds critical threshold
    """
    thresholds = ANOMALY_THRESHOLDS.get(sensor_type)
    if not thresholds:
        return False

    # Rule 1: Out of range
    if new_value < thresholds["min"] or new_value > thresholds["max"]:
        logger.warning(
            f"🚨 ANOMALY: {device_id}/{sensor_type} value {new_value} out of range "
            f"[{thresholds['min']}, {thresholds['max']}]"
        )
        return True

    # Rule 2: Sudden spike — compare with average of last 3 readings
    if thresholds.get("spike_pct"):
        cutoff = reading_at - timedelta(hours=3)
        result = await db.execute(
            select(func.avg(SensorReading.value))
            .where(SensorReading.device_id == device_id)
            .where(SensorReading.sensor_type == sensor_type)
            .where(SensorReading.reading_at >= cutoff)
            .where(SensorReading.reading_at < reading_at)
        )
        avg_recent = result.scalar()

        if avg_recent is not None and avg_recent > 0:
            change_pct = abs(new_value - avg_recent) / avg_recent * 100
            if change_pct > thresholds["spike_pct"]:
                logger.warning(
                    f"🚨 ANOMALY: {device_id}/{sensor_type} spike detected: "
                    f"{avg_recent:.1f} → {new_value:.1f} ({change_pct:.1f}% change)"
                )
                return True

    # Rule 3: Critical threshold
    if thresholds.get("critical_high") and new_value >= thresholds["critical_high"]:
        logger.warning(
            f"⚠️ CRITICAL: {device_id}/{sensor_type} value {new_value} exceeds "
            f"critical threshold {thresholds['critical_high']}"
        )
        return True

    return False


async def ingest_sensor_reading(
    db: AsyncSession,
    zone_id: int,
    device_id: str,
    sensor_type: str,
    value: float,
    unit: str,
    reading_at: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    battery_level: Optional[float] = None,
    signal_strength: Optional[float] = None,
) -> SensorReading:
    """
    Ingest a single sensor reading with anomaly detection.
    """
    # Check for anomalies
    is_anomaly = await check_reading_anomaly(
        db, zone_id, device_id, sensor_type, value, reading_at
    )

    # Build PostGIS point from lat/lng if provided
    location_wkt = f"SRID=4326;POINT({longitude} {latitude})" if latitude and longitude else None

    reading = SensorReading(
        zone_id=zone_id,
        device_id=device_id,
        sensor_type=sensor_type,
        value=value,
        unit=unit,
        location=location_wkt,
        battery_level=battery_level,
        signal_strength=signal_strength,
        is_anomaly=1 if is_anomaly else 0,
        reading_at=reading_at,
    )

    db.add(reading)
    await db.commit()
    await db.refresh(reading)

    if is_anomaly:
        logger.info(f"⚠️ Anomalous reading ingested: {reading}")
    else:
        logger.debug(f"✅ Sensor reading ingested: {reading}")

    return reading


async def ingest_batch_readings(
    db: AsyncSession,
    readings_data: list[dict],
) -> dict:
    """
    Batch ingest multiple sensor readings (used for offline sync).
    """
    ingested = 0
    anomalies = 0
    errors = 0

    for data in readings_data:
        try:
            reading = await ingest_sensor_reading(db, **data)
            ingested += 1
            if reading.is_anomaly:
                anomalies += 1
        except Exception as e:
            logger.error(f"Failed to ingest reading {data.get('device_id')}: {e}")
            errors += 1

    return {
        "ingested": ingested,
        "anomalies_detected": anomalies,
        "errors": errors,
    }


async def get_sensor_stats(
    db: AsyncSession, zone_id: int, sensor_type: str, hours: int = 24
) -> Optional[dict]:
    """
    Get aggregated stats for a sensor type in a zone over the last N hours.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(
            func.count(SensorReading.id),
            func.avg(SensorReading.value),
            func.min(SensorReading.value),
            func.max(SensorReading.value),
            func.max(SensorReading.reading_at),
        )
        .where(SensorReading.zone_id == zone_id)
        .where(SensorReading.sensor_type == sensor_type)
        .where(SensorReading.reading_at >= cutoff)
    )

    row = result.one_or_none()
    if not row or row[0] == 0:
        return None

    # Get latest reading
    latest_result = await db.execute(
        select(SensorReading.value)
        .where(SensorReading.zone_id == zone_id)
        .where(SensorReading.sensor_type == sensor_type)
        .order_by(SensorReading.reading_at.desc())
        .limit(1)
    )
    latest_value = latest_result.scalar()

    return {
        "zone_id": zone_id,
        "sensor_type": sensor_type,
        "latest_value": latest_value,
        "avg_value": round(float(row[1]), 2) if row[1] else None,
        "min_value": float(row[2]) if row[2] else None,
        "max_value": float(row[3]) if row[3] else None,
        "reading_count": row[0],
        "last_reading_at": row[4],
        "period_hours": hours,
    }
