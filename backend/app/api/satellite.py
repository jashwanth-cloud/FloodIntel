from fastapi import APIRouter, HTTPException
from ..geospatial.raster_utils import get_raster_metadata, calculate_flooded_area
import os
from datetime import datetime, timezone

router = APIRouter()

RASTER_PATH = "data/processed/feature04/validated_flood_label.tif"

@router.get("/satellite/flood/{location_id}")
async def get_satellite_flood(location_id: str):
    if location_id != "default": # Minimal location check for now
        raise HTTPException(status_code=404, detail="Location not found")
        
    if not os.path.exists(RASTER_PATH):
        raise HTTPException(status_code=500, detail="Satellite data unavailable")
        
    try:
        metadata = get_raster_metadata(RASTER_PATH)
        flooded_area = calculate_flooded_area(RASTER_PATH)
        
        return {
            "location_id": location_id,
            "event_id": "gfm_2024_09_01",
            "source": "Copernicus GFM",
            "data_state": "HISTORICAL",
            "observed_at": "2024-09-01T00:00:00Z",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "crs": metadata["crs"],
            "bounds": metadata["bounds"],
            "flooded_area_sqm": flooded_area,
            "provenance": "Derived from Sentinel-1 SAR",
            "observation_type": "SATELLITE_OBSERVED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
