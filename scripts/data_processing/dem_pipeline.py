"""
Phase 3 — Step 3: DEM Processing Pipeline
==========================================
Processes Digital Elevation Model data to derive terrain features.

Key findings from inspection:
  - Raw DEM directory is EMPTY (data/raw/dem/ has no files)
  - Processed DEM exists: data/processed/dem/dem_test_processed.tif
      CRS: EPSG:4326
      Bounds: left=4.0, bottom=12.0, right=5.0, top=13.0
      Shape: 3601×3601 pixels
      Resolution: ~0.000278° (~30m)
      NOTE: This appears to be a test tile (Africa/Indian Ocean region, NOT the Andhra Pradesh AOI)

DEM strategy:
  - The only DEM available is the test tile.
  - The flood AOI is at bounds: left=80.39, bottom=16.26, right=80.49, top=16.36
  - The DEM test tile does NOT overlap the flood AOI geographically.
  - Therefore, full DEM-to-AOI intersection cannot be performed.
  - We document this limitation and produce a skeleton elevation feature schema.

Slope calculation method:
  - Uses numpy gradient (finite differences) since richdem is not installable.
  - Converts degrees to approximate meters for gradient calculation.

Outputs:
  data/features/dem_features.parquet  — terrain features for the DEM tile (available)
  docs/dem_limitation_note.txt        — limitation documentation
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("dem_pipeline")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEM_RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "dem")
DEM_PROC_DIR = os.path.join(BASE_DIR, "data", "processed", "dem")
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
os.makedirs(FEATURES_DIR, exist_ok=True)

FLOOD_AOI_BOUNDS = {
    "left": 80.3865,
    "bottom": 16.2567,
    "right": 80.4865,
    "top": 16.3567,
}


def compute_slope_from_array(elevation, res_x_deg, res_y_deg):
    """
    Compute slope (in degrees) from an elevation array using numpy gradient.

    Parameters
    ----------
    elevation : 2D ndarray, shape (rows, cols)
    res_x_deg : float — pixel size in degrees (x/longitude direction)
    res_y_deg : float — pixel size in degrees (y/latitude direction, positive)

    Returns
    -------
    slope_deg : 2D ndarray of slope in degrees
    """
    # Approximate conversion: 1 degree latitude ≈ 111,320 m
    res_x_m = res_x_deg * 111320.0
    res_y_m = res_y_deg * 111320.0

    # Gradient (dz/dy, dz/dx)
    dz_dy, dz_dx = np.gradient(elevation, res_y_m, res_x_m)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = np.degrees(slope_rad)
    return slope_deg


def process_dem_tile(tif_path, sample_only=False):
    """
    Process a DEM TIF and return a DataFrame with elevation/slope features.

    Parameters
    ----------
    tif_path : str — path to DEM GeoTIFF
    sample_only : bool — if True, only return a 100×100 corner sample

    Returns
    -------
    df : pd.DataFrame with columns: lat, lon, elevation_m, slope_deg
    meta : dict with raster metadata
    """
    log.info(f"Reading DEM: {tif_path}")

    with rasterio.open(tif_path) as src:
        meta = {
            "crs": str(src.crs),
            "bounds": list(src.bounds),
            "width": src.width,
            "height": src.height,
            "nodata": src.nodata,
            "dtype": str(src.dtypes[0]),
            "resolution_deg": [abs(src.transform.a), abs(src.transform.e)],
            "transform": list(src.transform),
        }
        res_x = abs(src.transform.a)
        res_y = abs(src.transform.e)

        # Read elevation band
        elev = src.read(1, masked=True)  # shape: (height, width)
        nodata = src.nodata
        left, bottom, right, top = src.bounds

        if sample_only:
            # Take a 100×100 corner sample
            elev = elev[:100, :100]
            rows_slice = slice(0, 100)
            cols_slice = slice(0, 100)
            nrows, ncols = 100, 100
        else:
            nrows, ncols = elev.shape

        log.info(f"DEM array shape: {elev.shape}, nodata: {nodata}")

    # Compute lat/lon grid
    lats = top - (np.arange(nrows) + 0.5) * res_y   # row → latitude (descending N→S)
    lons = left + (np.arange(ncols) + 0.5) * res_x  # col → longitude (ascending W→E)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Elevation as float, NaN for nodata
    elev_arr = elev.filled(np.nan) if hasattr(elev, "filled") else np.array(elev, dtype=float)
    if nodata is not None:
        elev_arr[elev_arr == nodata] = np.nan

    # Slope
    log.info("Computing slope...")
    valid_elev = np.where(np.isnan(elev_arr), 0.0, elev_arr)  # fill NaN with 0 for gradient
    slope_deg = compute_slope_from_array(valid_elev, res_x, res_y)
    slope_deg[np.isnan(elev_arr)] = np.nan

    # Flatten to DataFrame
    mask_valid = ~np.isnan(elev_arr)
    df = pd.DataFrame({
        "lat": lat_grid[mask_valid].astype(np.float32),
        "lon": lon_grid[mask_valid].astype(np.float32),
        "elevation_m": elev_arr[mask_valid].astype(np.float32),
        "slope_deg": slope_deg[mask_valid].astype(np.float32),
    })

    log.info(f"DEM features: {len(df):,} valid pixels")
    log.info(f"Elevation: min={df['elevation_m'].min():.1f}, max={df['elevation_m'].max():.1f} m")
    log.info(f"Slope: min={df['slope_deg'].min():.3f}, max={df['slope_deg'].max():.3f} °")

    return df, meta


def check_dem_aoi_overlap(dem_bounds, aoi_bounds):
    """Check whether a DEM tile overlaps the flood AOI."""
    dem_left, dem_bottom, dem_right, dem_top = dem_bounds
    aoi_left = aoi_bounds["left"]
    aoi_bottom = aoi_bounds["bottom"]
    aoi_right = aoi_bounds["right"]
    aoi_top = aoi_bounds["top"]

    x_overlap = (dem_left < aoi_right) and (dem_right > aoi_left)
    y_overlap = (dem_bottom < aoi_top) and (dem_top > aoi_bottom)
    return x_overlap and y_overlap


def write_limitation_note():
    """Document the DEM limitation clearly."""
    note_path = os.path.join(BASE_DIR, "docs", "dem_limitation_note.txt")
    content = """DEM DATA LIMITATION — Phase 3 Assessment
==========================================

FINDING:
  The raw DEM directory (data/raw/dem/) is EMPTY.
  No source DEM tiles have been downloaded for the flood AOI.

  The only DEM file present is:
    data/processed/dem/dem_test_processed.tif
    - CRS: EPSG:4326
    - Bounds: left=3.999861, bottom=11.999861, right=5.000139, top=13.000139
    - Resolution: ~0.000278° (~30m)
    - Shape: 3601×3601 pixels
    - Likely source: SRTM30 test tile from Africa/Atlantic region

  The flood AOI (Andhra Pradesh study area) is at:
    Bounds: left=80.3865, bottom=16.2567, right=80.4865, top=16.3567
    (Longitude ~80.4°E, Latitude ~16.3°N)

  The DEM test tile and the flood AOI DO NOT OVERLAP geographically.

IMPACT:
  - Elevation and slope features CANNOT be computed for the flood AOI from
    the currently available DEM.
  - DEM-based flood feature columns (elevation_m, slope_deg) will be
    marked as NULL/NaN in the final feature dataset.

RECOMMENDATION FOR PHASE 4:
  Download SRTM 30m or Copernicus DEM 30m tiles for the target AOI.
  The download_dem.py script in scripts/ may handle this.
  Run: python scripts/download_dem.py --lat 16.25 --lon 80.38 --radius 0.15

TERRAIN FEATURES PLANNED (schema reserved):
  - elevation_m        : mean elevation in metres
  - slope_deg          : mean terrain slope in degrees
  - elevation_min_m    : minimum elevation
  - elevation_max_m    : maximum elevation
  - elevation_range_m  : elevation range (terrain roughness proxy)
"""
    os.makedirs(os.path.dirname(note_path), exist_ok=True)
    with open(note_path, "w") as f:
        f.write(content)
    log.info(f"DEM limitation note written to: {note_path}")


def run_dem_pipeline(sample_only=False):
    """
    Full DEM pipeline.
    Processes the available test DEM, checks AOI overlap, and documents limitations.
    """
    log.info("=" * 60)
    log.info("PHASE 3 — DEM Pipeline")
    log.info("=" * 60)

    # Check raw DEM
    raw_files = [f for f in os.listdir(DEM_RAW_DIR)] if os.path.isdir(DEM_RAW_DIR) else []
    log.info(f"Raw DEM files: {raw_files}")
    if not raw_files:
        log.warning("Raw DEM directory is EMPTY — no source DEM tiles available.")

    # Check processed test DEM
    test_dem = os.path.join(DEM_PROC_DIR, "dem_test_processed.tif")
    if not os.path.exists(test_dem):
        log.error(f"Test DEM not found at {test_dem}")
        write_limitation_note()
        return None, None

    # Check AOI overlap
    with rasterio.open(test_dem) as src:
        dem_bounds = src.bounds

    overlaps = check_dem_aoi_overlap(dem_bounds, FLOOD_AOI_BOUNDS)
    log.info(f"DEM test tile bounds: {dem_bounds}")
    log.info(f"Flood AOI bounds: {FLOOD_AOI_BOUNDS}")
    log.info(f"DEM overlaps Flood AOI: {overlaps}")

    if not overlaps:
        log.warning("DEM test tile DOES NOT overlap flood AOI. Writing limitation note.")
        write_limitation_note()

    # Still process the test DEM to validate the pipeline itself
    log.info("Processing available DEM tile (for pipeline validation)...")
    df, meta = process_dem_tile(test_dem, sample_only=sample_only)

    # Save to features directory
    out_path = os.path.join(FEATURES_DIR, "dem_test_features.parquet")
    df.to_parquet(out_path, index=False)
    log.info(f"Saved test DEM features: {out_path} ({os.path.getsize(out_path)/1e6:.3f} MB)")
    log.info(f"Shape: {df.shape}")

    # Summary
    log.info("=" * 60)
    log.info("DEM Pipeline complete.")
    log.info("NOTE: No DEM coverage for flood AOI. See docs/dem_limitation_note.txt")
    log.info("=" * 60)

    return df, meta


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DEM Processing Pipeline")
    parser.add_argument("--sample", action="store_true", help="Process only a small sample")
    args = parser.parse_args()
    run_dem_pipeline(sample_only=args.sample)
