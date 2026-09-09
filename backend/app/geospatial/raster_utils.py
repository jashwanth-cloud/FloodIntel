import rasterio
import numpy as np
from typing import Dict, Any, Optional

def get_raster_metadata(file_path: str) -> Dict[str, Any]:
    """Reads and returns metadata for a given raster file."""
    try:
        with rasterio.open(file_path) as src:
            return {
                "crs": str(src.crs),
                "bounds": [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top],
                "width": src.width,
                "height": src.height,
                "transform": list(src.transform)
            }
    except Exception as e:
        raise ValueError(f"Error reading raster metadata: {str(e)}")

def calculate_flooded_area(file_path: str) -> float:
    """Calculates the flooded area in square meters from the raster."""
    try:
        with rasterio.open(file_path) as src:
            # Assuming binary flood map where 1 is flooded
            data = src.read(1)
            # Count pixels with value 1
            flooded_pixels = np.sum(data == 1)
            # Multiply by pixel resolution (assuming square pixels)
            # Need to get resolution from transform
            res_x = src.res[0]
            res_y = src.res[1]
            return float(flooded_pixels * res_x * res_y)
    except Exception as e:
        raise ValueError(f"Error calculating flooded area: {str(e)}")
