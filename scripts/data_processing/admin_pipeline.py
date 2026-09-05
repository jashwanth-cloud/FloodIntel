"""
Phase 3 — Step 5: Ward/Administrative Boundary Assessment + Feature Join
=========================================================================
Checks for ward/administrative boundary data and either performs a spatial
join or clearly documents the missing dependency.

Finding from inspection:
  - No ward, district, or municipality boundary files found in the project.
  - Only file matching 'state' keyword: surface_waterbodies_state_index.json
    (this is a waterbody state index, NOT administrative boundaries)
  - No shapefiles (.shp), GeoPackages (.gpkg), or admin GeoJSONs exist.

Decision:
  CANNOT perform ward-level aggregation — boundaries are missing.
  This script documents the gap clearly and creates a placeholder schema.

If ward boundaries are later obtained:
  - Place the file at: data/raw/admin/india_ward_boundaries.geojson
  - Re-run this script.
  - It will automatically detect and process the file.

Outputs:
  docs/WARD_BOUNDARIES_MISSING.md   — missing dependency documentation
  data/features/admin_features.parquet — skeleton (empty) with schema
"""

import os
import logging
import numpy as np
import pandas as pd
import geopandas as gpd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("admin_pipeline")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
ADMIN_DIR = os.path.join(BASE_DIR, "data", "raw", "admin")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(FEATURES_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# Candidate paths for ward boundaries (will be checked in order)
ADMIN_CANDIDATES = [
    os.path.join(ADMIN_DIR, "india_ward_boundaries.geojson"),
    os.path.join(ADMIN_DIR, "india_ward_boundaries.shp"),
    os.path.join(ADMIN_DIR, "india_ward_boundaries.gpkg"),
    os.path.join(BASE_DIR, "data", "raw", "india_ward_boundaries.geojson"),
    os.path.join(BASE_DIR, "metadata", "india_ward_boundaries.geojson"),
]

AOI_BOUNDS = (80.3865, 16.2567, 80.4865, 16.3567)


def find_admin_boundary():
    """Check all candidate paths for ward boundary files."""
    for path in ADMIN_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def write_missing_doc():
    """Write a clear documentation file about the missing ward boundaries."""
    doc_path = os.path.join(DOCS_DIR, "WARD_BOUNDARIES_MISSING.md")
    content = """# Ward Boundary Data — Missing Dependency

## Status: ⛔ MISSING

No ward, district, or municipality boundary files were found in this project.

## What Was Searched

The following locations were checked and found empty:

- `data/raw/admin/`
- `data/raw/india_ward_boundaries.*`
- `metadata/india_ward_boundaries.*`
- All files in the project matching keywords: ward, admin, district, municipality, taluk

## Only Admin-Related File Found

`data/raw/hydrology/water_bodies/reports/surface_waterbodies_state_index.json`

This is NOT an administrative boundary file. It is a state-level index of
surface waterbody processing reports, not geometry boundaries.

## Impact on Phase 3

The following planned features CANNOT be computed without ward boundaries:

| Feature | Status |
|---------|--------|
| ward_id | ❌ Not possible |
| district_id | ❌ Not possible |
| state_id | ❌ Not possible |
| Ward-level rainfall aggregation | ❌ Not possible |
| Ward-level DEM aggregation | ❌ Not possible |
| Ward-level waterbody features | ❌ Not possible |
| Ward-level flood risk score | ❌ Not possible |

## What CAN Be Done

Environmental features (rainfall, DEM, waterbody proximity) CAN be computed
at the **grid-cell level** (lat/lon point) and at the **flood AOI raster level**.
These can later be aggregated to ward level once boundaries are obtained.

## Recommended Action for Phase 4

Obtain administrative boundary data from one of the following sources:

1. **GADM** (Global Administrative Areas):
   - URL: https://gadm.org/download_country.html
   - Select India (IND), Level 3 (district) or Level 4 (sub-district/taluk)
   - Format: GeoJSON or Shapefile

2. **Bhuvan / Survey of India**:
   - URL: https://bhuvan.nrsc.gov.in/
   - Open government geospatial portal for India

3. **Open Government Data Platform India**:
   - URL: https://data.gov.in/
   - Search for "ward boundaries" or "municipal boundaries"

4. **Municipal corporation websites** (if specific city):
   - e.g., VMRDA (Vijayawada Metropolitan Region Development Authority)
   - The AOI appears to be near Vijayawada, Andhra Pradesh

## File Placement

Once obtained, place the file at:
```
data/raw/admin/india_ward_boundaries.geojson
```
Then re-run:
```bash
python scripts/data_processing/admin_pipeline.py
```

## Current Fallback

The feature dataset uses grid-cell level lat/lon as geographic identifiers
instead of ward IDs. When ward boundaries become available, a spatial join
can be performed to assign ward_id, district_id, etc. to each grid cell.
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    log.info(f"Written: {doc_path}")
    return doc_path


def create_skeleton_admin_features():
    """
    Create an empty DataFrame with the intended admin feature schema.
    Columns will be NaN/None until ward boundaries are available.
    """
    schema = pd.DataFrame(columns=[
        "ward_id",
        "district_id",
        "state_id",
        "ward_name",
        "district_name",
        "state_name",
        "ward_lat_centroid",
        "ward_lon_centroid",
        "ward_area_km2",
    ])
    # Explicitly set dtypes
    schema = schema.astype({
        "ward_id": "object",
        "district_id": "object",
        "state_id": "object",
        "ward_name": "object",
        "district_name": "object",
        "state_name": "object",
        "ward_lat_centroid": "float64",
        "ward_lon_centroid": "float64",
        "ward_area_km2": "float64",
    })
    return schema


def process_ward_boundaries(boundary_path):
    """
    Process ward boundary file if found.
    Validates geometry, CRS, and produces admin feature schema.
    """
    log.info(f"Loading ward boundaries from: {boundary_path}")
    gdf = gpd.read_file(boundary_path, bbox=AOI_BOUNDS)

    if gdf.crs is None:
        log.warning("  CRS is None — assuming EPSG:4326")
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        log.info(f"  Reprojecting from {gdf.crs} to EPSG:4326")
        gdf = gdf.to_crs("EPSG:4326")

    log.info(f"  Loaded {len(gdf)} ward features")
    log.info(f"  Columns: {list(gdf.columns)}")

    # Repair invalid geometries
    invalid = (~gdf.geometry.is_valid).sum()
    if invalid > 0:
        log.warning(f"  {invalid} invalid geometries — repairing with buffer(0)")
        gdf.geometry = gdf.geometry.buffer(0)

    # Compute centroid and area
    gdf_proj = gdf.to_crs("EPSG:32644")
    gdf["ward_lat_centroid"] = gdf.geometry.centroid.y.astype(np.float32)
    gdf["ward_lon_centroid"] = gdf.geometry.centroid.x.astype(np.float32)
    gdf["ward_area_km2"] = (gdf_proj.geometry.area / 1e6).astype(np.float32)

    return gdf


def run_admin_pipeline():
    """
    Full admin/ward boundary pipeline.
    """
    log.info("=" * 60)
    log.info("PHASE 3 — Admin/Ward Boundary Pipeline")
    log.info("=" * 60)

    boundary_path = find_admin_boundary()

    if boundary_path is None:
        log.warning("No ward boundary files found.")
        write_missing_doc()
        # Create skeleton schema
        skeleton = create_skeleton_admin_features()
        out_path = os.path.join(FEATURES_DIR, "admin_features_skeleton.parquet")
        skeleton.to_parquet(out_path, index=False)
        log.info(f"Skeleton schema written to: {out_path}")
        log.info("Admin pipeline stopped — missing dependency documented.")
        return None
    else:
        log.info(f"Ward boundaries found at: {boundary_path}")
        gdf = process_ward_boundaries(boundary_path)

        out_path = os.path.join(FEATURES_DIR, "admin_features.parquet")
        gdf.drop(columns=["geometry"]).to_parquet(out_path, index=False)
        log.info(f"Admin features saved: {out_path}")
        return gdf


if __name__ == "__main__":
    run_admin_pipeline()
