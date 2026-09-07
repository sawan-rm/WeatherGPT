"""
Satellite data service — interfaces with Sentinel-2 and ISRO Bhuvan APIs.
Processes satellite imagery to detect vegetation changes (NDVI), soil moisture,
and slope movement indicators relevant to landslide prediction.

NOTE: For a personal project, we use free Copernicus Data Space APIs.
Full satellite processing (GeoTIFF) is heavy — this service provides
the API integration layer. Actual image processing would use rasterio/GDAL.
"""
import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Sentinel-2 Copernicus Data Space Ecosystem (free)
COPERNICUS_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

# NER bounding box (approximate)
NER_BBOX = {
    "west": 88.0,   # Western boundary (Sikkim)
    "south": 22.0,   # Southern boundary (Tripura/Mizoram)
    "east": 97.5,    # Eastern boundary (Arunachal)
    "north": 29.5,   # Northern boundary (Arunachal)
}


async def search_sentinel2_products(
    days_back: int = 7,
    cloud_cover_max: int = 30,
    state_bbox: Optional[dict] = None,
) -> list[dict]:
    """
    Search for recent Sentinel-2 satellite products covering the NER.
    Uses Copernicus Data Space OData API (free, no API key needed for search).
    
    Returns list of available products with download links.
    """
    bbox = state_bbox or NER_BBOX
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00.000Z")
    end_date = now.strftime("%Y-%m-%dT23:59:59.999Z")

    # OData filter for Sentinel-2 L2A (atmospherically corrected)
    filter_str = (
        f"Collection/Name eq 'SENTINEL-2' "
        f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' "
        f"and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') "
        f"and ContentDate/Start gt {start_date} "
        f"and ContentDate/Start lt {end_date} "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(("
        f"{bbox['west']} {bbox['south']},"
        f"{bbox['east']} {bbox['south']},"
        f"{bbox['east']} {bbox['north']},"
        f"{bbox['west']} {bbox['north']},"
        f"{bbox['west']} {bbox['south']}"
        f"))') "
    )

    url = f"{COPERNICUS_CATALOG_URL}/Products"
    params = {
        "$filter": filter_str,
        "$top": 20,
        "$orderby": "ContentDate/Start desc",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        products = []
        for item in data.get("value", []):
            products.append({
                "id": item.get("Id"),
                "name": item.get("Name"),
                "sensing_date": item.get("ContentDate", {}).get("Start"),
                "cloud_cover": item.get("Attributes", {}).get("cloudCover"),
                "footprint": item.get("GeoFootprint"),
                "size_mb": round(item.get("ContentLength", 0) / (1024 * 1024), 1),
                "online": item.get("Online", False),
            })

        logger.info(f"Found {len(products)} Sentinel-2 products for NER (last {days_back} days)")
        return products

    except httpx.HTTPError as e:
        logger.error(f"Copernicus API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Satellite search error: {e}")
        return []


def compute_ndvi_change_indicator(ndvi_current: float, ndvi_baseline: float) -> dict:
    """
    Compute NDVI (Normalized Difference Vegetation Index) change.
    A drop in NDVI can indicate deforestation, soil erosion, or slope movement.
    
    NDVI ranges: -1 to 1 (0.2-0.4 = sparse veg, 0.6-0.9 = dense forest)
    
    NOTE: In production, actual NDVI is calculated from satellite bands:
    NDVI = (NIR - Red) / (NIR + Red) using Band 8 (NIR) and Band 4 (Red)
    This function processes pre-computed NDVI values.
    """
    change = ndvi_current - ndvi_baseline
    change_pct = (change / ndvi_baseline * 100) if ndvi_baseline != 0 else 0

    if change_pct < -20:
        risk_indicator = "critical"  # Major vegetation loss
    elif change_pct < -10:
        risk_indicator = "high"
    elif change_pct < -5:
        risk_indicator = "medium"
    else:
        risk_indicator = "low"

    return {
        "ndvi_current": ndvi_current,
        "ndvi_baseline": ndvi_baseline,
        "ndvi_change": round(change, 4),
        "change_pct": round(change_pct, 2),
        "risk_indicator": risk_indicator,
    }


def compute_soil_moisture_from_indices(
    ndwi: float, ndmi: float
) -> dict:
    """
    Estimate soil moisture conditions from satellite-derived indices.
    
    NDWI (Normalized Difference Water Index): detects surface water/moisture
    NDMI (Normalized Difference Moisture Index): detects vegetation moisture content
    
    High values indicate saturated conditions → higher landslide risk.
    """
    # Combined moisture indicator
    moisture_index = (ndwi + ndmi) / 2

    if moisture_index > 0.5:
        risk_indicator = "critical"
        description = "Extremely saturated conditions"
    elif moisture_index > 0.3:
        risk_indicator = "high"
        description = "High soil moisture, approaching saturation"
    elif moisture_index > 0.1:
        risk_indicator = "medium"
        description = "Moderate soil moisture"
    else:
        risk_indicator = "low"
        description = "Normal soil moisture levels"

    return {
        "ndwi": ndwi,
        "ndmi": ndmi,
        "moisture_index": round(moisture_index, 4),
        "risk_indicator": risk_indicator,
        "description": description,
    }


async def get_satellite_status() -> dict:
    """
    Check the status of satellite data availability for NER.
    Used by the dashboard to show data freshness.
    """
    recent_products = await search_sentinel2_products(days_back=3)

    return {
        "available_products_3d": len(recent_products),
        "latest_product": recent_products[0] if recent_products else None,
        "ner_coverage": "partial" if recent_products else "no_recent_data",
        "note": "Sentinel-2 revisit time: ~5 days per location",
    }
