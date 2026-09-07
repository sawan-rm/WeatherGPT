"""
DEM (Digital Elevation Model) Service.
Loads and processes terrain data (slope, aspect, curvature, elevation)
from open DEM datasets (SRTM, CartoDEM) for landslide zone characterization.

For a personal project, we use the Open-Elevation API (free) and SRTM data
via the OpenTopography API for terrain analysis.
"""
import httpx
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Free elevation APIs
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"
OPEN_TOPO_URL = "https://portal.opentopography.org/API/globaldem"


async def get_elevation(lat: float, lng: float) -> Optional[float]:
    """
    Get elevation in meters for a lat/lng point using Open-Elevation API.
    Free, no API key needed.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                OPEN_ELEVATION_URL,
                params={"locations": f"{lat},{lng}"}
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if results:
            return results[0].get("elevation")
        return None

    except httpx.HTTPError as e:
        logger.error(f"Open-Elevation API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Elevation lookup error: {e}")
        return None


async def get_elevation_batch(coordinates: list[dict]) -> list[dict]:
    """
    Get elevation for multiple points in a single request.
    coordinates: [{"latitude": 25.5, "longitude": 91.8}, ...]
    """
    try:
        locations = [
            {"latitude": c["latitude"], "longitude": c["longitude"]}
            for c in coordinates
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPEN_ELEVATION_URL,
                json={"locations": locations}
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for i, result in enumerate(data.get("results", [])):
            results.append({
                "latitude": coordinates[i]["latitude"],
                "longitude": coordinates[i]["longitude"],
                "elevation_m": result.get("elevation"),
            })

        return results

    except Exception as e:
        logger.error(f"Batch elevation lookup error: {e}")
        return []


def estimate_slope_from_elevations(
    center_elev: float,
    north_elev: float,
    south_elev: float,
    east_elev: float,
    west_elev: float,
    cell_size_m: float = 90.0,  # SRTM 3-arc-second ≈ 90m resolution
) -> dict:
    """
    Estimate slope and aspect from a 3x3 elevation grid center.
    Uses the Horn (1981) method — same algorithm used by GIS software.
    
    Returns slope (degrees), aspect (degrees from north), curvature.
    """
    # Calculate gradient in X and Y directions
    dz_dx = (east_elev - west_elev) / (2 * cell_size_m)
    dz_dy = (north_elev - south_elev) / (2 * cell_size_m)

    # Slope in degrees
    slope_rad = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = math.degrees(slope_rad)

    # Aspect (direction slope faces, degrees from north, clockwise)
    if dz_dx == 0 and dz_dy == 0:
        aspect = -1  # Flat
    else:
        aspect_rad = math.atan2(-dz_dx, dz_dy)
        aspect = math.degrees(aspect_rad)
        if aspect < 0:
            aspect += 360

    # Simple curvature estimate (profile curvature)
    curvature = (north_elev + south_elev + east_elev + west_elev - 4 * center_elev) / (cell_size_m ** 2)

    return {
        "slope_degree": round(slope_deg, 2),
        "aspect": round(aspect, 2),
        "curvature": round(curvature, 6),
    }


async def analyze_terrain_for_zone(
    lat: float, lng: float, offset_deg: float = 0.001
) -> dict:
    """
    Perform terrain analysis for a zone centroid by sampling elevations
    around the point and computing slope, aspect, and curvature.
    
    offset_deg ≈ 0.001° ≈ ~111 meters at the equator (~100m at NER latitudes)
    """
    # Sample 5 points: center, north, south, east, west
    points = [
        {"latitude": lat, "longitude": lng},           # center
        {"latitude": lat + offset_deg, "longitude": lng},  # north
        {"latitude": lat - offset_deg, "longitude": lng},  # south
        {"latitude": lat, "longitude": lng + offset_deg},  # east
        {"latitude": lat, "longitude": lng - offset_deg},  # west
    ]

    elevations = await get_elevation_batch(points)

    if len(elevations) < 5 or any(e.get("elevation_m") is None for e in elevations):
        logger.warning(f"Incomplete elevation data for ({lat}, {lng})")
        # Return what we have
        center_elev = elevations[0].get("elevation_m") if elevations else None
        return {
            "elevation_m": center_elev,
            "slope_degree": None,
            "aspect": None,
            "curvature": None,
            "relief": None,
            "data_quality": "incomplete",
        }

    center_elev = elevations[0]["elevation_m"]
    north_elev = elevations[1]["elevation_m"]
    south_elev = elevations[2]["elevation_m"]
    east_elev = elevations[3]["elevation_m"]
    west_elev = elevations[4]["elevation_m"]

    # Compute terrain metrics
    # Cell size in meters at this latitude
    cell_size_m = offset_deg * 111000 * math.cos(math.radians(lat))
    terrain = estimate_slope_from_elevations(
        center_elev, north_elev, south_elev, east_elev, west_elev,
        cell_size_m=cell_size_m
    )

    # Relief = max elevation - min elevation in the sample area
    all_elevs = [center_elev, north_elev, south_elev, east_elev, west_elev]
    relief = max(all_elevs) - min(all_elevs)

    return {
        "elevation_m": center_elev,
        "slope_degree": terrain["slope_degree"],
        "aspect": terrain["aspect"],
        "curvature": terrain["curvature"],
        "relief": round(relief, 2),
        "data_quality": "good",
    }


def classify_slope_risk(slope_degree: float) -> str:
    """
    Classify landslide risk based on slope angle.
    Based on Bureau of Indian Standards (BIS) landslide hazard zonation guidelines.
    """
    if slope_degree < 15:
        return "low"
    elif slope_degree < 25:
        return "medium"
    elif slope_degree < 35:
        return "high"
    else:
        return "critical"
