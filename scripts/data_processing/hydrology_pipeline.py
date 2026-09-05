"""
Phase 3 — Step 4: Waterbody / Hydrology Processing Pipeline
=============================================================
Processes large GIS datasets efficiently to compute waterbody and
river proximity features.

Key dataset sizes:
  - waterbodies_india.geojson :  5,074.95 MB  (5.07 GB) — TOO LARGE for full RAM load
  - india_river_network.geojson : 356.23 MB
  - india_canal_network.geojson : 233.10 MB
  - india_reservoirs_source.geojson : 452.53 MB
  - basin_cwc.GeoJSON : 17.48 MB

Strategy:
  Since fiona is not installed, we use geopandas (which wraps pyogrio/fiona internally).
  For the 5.07 GB waterbody file, we use chunked reading with geopandas via
  pyogrio engine if available, otherwise we implement a streaming JSON parser.

  For the flood AOI (small area ~10×10 km), we can:
    1. Attempt bbox-filtered reads using geopandas read_file with bbox parameter.
    2. Fall back to line-by-line GeoJSON streaming for the huge file.

  Output: Distance-to-nearest-waterbody and distance-to-nearest-river
          for a grid of points covering the flood AOI.

Flood AOI confirmed: EPSG:4326, ~80.39–80.49°E, ~16.26–16.36°N (Andhra Pradesh)

Outputs:
  data/features/hydrology_features_aoi.parquet — proximity features for AOI grid
"""

import os
import sys
import json
import math
import logging
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box, shape
from shapely.ops import nearest_points

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("hydrology_pipeline")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HYDRO_DIR = os.path.join(BASE_DIR, "data", "raw", "hydrology")
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
os.makedirs(FEATURES_DIR, exist_ok=True)

# AOI bounds (confirmed from satellite_features.tif inspection)
AOI_BOUNDS = (80.3865, 16.2567, 80.4865, 16.3567)  # (minx, miny, maxx, maxy)
AOI_BUFFER_DEG = 0.05  # ~5.5 km buffer for proximity calculations

WATERBODY_PATH = os.path.join(HYDRO_DIR, "water_bodies", "india", "india_surface_waterbodies.geojson")
RIVER_PATH = os.path.join(HYDRO_DIR, "rivers", "india_river_network.geojson")
CANAL_PATH = os.path.join(HYDRO_DIR, "drainage", "india_canal_network.geojson")
RESERVOIR_PATH = os.path.join(HYDRO_DIR, "reservoirs", "india_reservoirs_source.geojson")
BASIN_PATH = os.path.join(HYDRO_DIR, "river_basins", "extracted", "basin_cwc.GeoJSON")


def haversine_distance_m(lat1, lon1, lat2, lon2):
    """Compute haversine distance in metres between two lat/lon points."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def deg_to_metres(degrees, mid_lat=16.3):
    """Rough conversion from degrees to metres at a given latitude."""
    return degrees * 111320 * math.cos(math.radians(mid_lat))


def make_aoi_grid(bounds, grid_spacing_deg=0.01):
    """
    Create a regular grid of points covering the AOI.
    Used as query points for proximity calculations.

    Returns a GeoDataFrame with point geometry, lat, lon columns.
    """
    minx, miny, maxx, maxy = bounds
    lons = np.arange(minx, maxx, grid_spacing_deg)
    lats = np.arange(miny, maxy, grid_spacing_deg)
    pts = []
    for lat in lats:
        for lon in lons:
            pts.append({"lat": lat, "lon": lon, "geometry": Point(lon, lat)})
    gdf = gpd.GeoDataFrame(pts, crs="EPSG:4326")
    return gdf


def load_geojson_bbox_safe(path, bbox, label="GeoJSON"):
    """
    Safely load a GeoJSON file filtered to a bounding box.
    Uses geopandas with bbox filter — avoids loading the full file.
    Falls back to streaming JSON parse if geopandas fails.
    """
    log.info(f"Loading {label} ({os.path.getsize(path)/1e6:.1f} MB) with bbox filter...")

    if not os.path.exists(path):
        log.error(f"  File not found: {path}")
        return None

    # Try geopandas with bbox (pyogrio or fiona backend)
    try:
        gdf = gpd.read_file(path, bbox=bbox, engine="pyogrio")
        log.info(f"  Loaded {len(gdf)} features via pyogrio bbox filter")
        return gdf
    except Exception as e1:
        log.warning(f"  pyogrio failed: {e1}")

    try:
        gdf = gpd.read_file(path, bbox=bbox)
        log.info(f"  Loaded {len(gdf)} features via default geopandas bbox filter")
        return gdf
    except Exception as e2:
        log.warning(f"  Default geopandas failed: {e2}")

    # Last resort: streaming line-by-line JSON parse
    log.info(f"  Falling back to streaming GeoJSON parse for {label}...")
    return _stream_geojson_bbox(path, bbox)


def _stream_geojson_bbox(path, bbox):
    """
    Memory-efficient streaming GeoJSON parser.
    Reads the file line by line looking for feature objects within bbox.

    For the 5.07 GB waterbody file this is slow but safe.
    Returns a GeoDataFrame of matching features.
    """
    minx, miny, maxx, maxy = bbox
    bbox_geom = box(minx, miny, maxx, maxy)

    features = []
    in_feature = False
    brace_depth = 0
    current_lines = []

    log.info(f"  Streaming {path}...")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f):
                stripped = line.strip()

                # Track brace depth to detect feature boundaries
                brace_depth += stripped.count("{") - stripped.count("}")

                if '"type": "Feature"' in stripped or '"type":"Feature"' in stripped:
                    in_feature = True
                    current_lines = []

                if in_feature:
                    current_lines.append(line)

                if in_feature and brace_depth == 1 and len(current_lines) > 1:
                    # Likely end of a feature object
                    feature_text = "".join(current_lines).strip().rstrip(",")
                    try:
                        feat = json.loads(feature_text)
                        geom = shape(feat["geometry"])
                        if geom.intersects(bbox_geom):
                            features.append(feat)
                    except (json.JSONDecodeError, KeyError, Exception):
                        pass
                    in_feature = False
                    current_lines = []

                if line_no % 1_000_000 == 0 and line_no > 0:
                    log.info(f"    Lines scanned: {line_no:,}, Features found: {len(features)}")

    except Exception as e:
        log.error(f"  Streaming error: {e}")

    if not features:
        log.warning(f"  No features found within bbox via streaming")
        return None

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    log.info(f"  Streaming complete: {len(gdf)} features found")
    return gdf


def compute_distance_to_nearest(query_gdf, target_gdf, feature_col_name, crs_metres="EPSG:32644"):
    """
    Compute distance in metres from each query point to nearest feature in target_gdf.

    Uses projected CRS (UTM Zone 44N for Andhra Pradesh area) for accurate distances.

    Parameters
    ----------
    query_gdf : GeoDataFrame of query points (EPSG:4326)
    target_gdf : GeoDataFrame of target features (EPSG:4326)
    feature_col_name : str — output column name (e.g. 'dist_waterbody_m')
    crs_metres : str — projected CRS for distance calculation

    Returns
    -------
    query_gdf with new column added
    """
    if target_gdf is None or len(target_gdf) == 0:
        log.warning(f"  No target features for {feature_col_name} — setting to NaN")
        query_gdf[feature_col_name] = np.nan
        return query_gdf

    log.info(f"  Computing {feature_col_name} for {len(query_gdf)} query points...")

    # Project to metres
    q_proj = query_gdf.to_crs(crs_metres)
    t_proj = target_gdf.to_crs(crs_metres)

    # Compute distances using spatial index
    t_union = t_proj.geometry.union_all() if hasattr(t_proj.geometry, "union_all") else t_proj.geometry.unary_union

    distances = q_proj.geometry.apply(
        lambda pt: pt.distance(t_union)
    )
    query_gdf = query_gdf.copy()
    query_gdf[feature_col_name] = distances.values.astype(np.float32)
    log.info(f"  {feature_col_name}: min={distances.min():.1f}m, max={distances.max():.1f}m, mean={distances.mean():.1f}m")
    return query_gdf


def compute_waterbody_coverage(query_gdf, waterbody_gdf, radius_m=500, crs_metres="EPSG:32644"):
    """
    Compute the fraction of area within `radius_m` that is covered by waterbodies.

    For each query point, creates a buffer and computes intersection area fraction.
    """
    if waterbody_gdf is None or len(waterbody_gdf) == 0:
        log.warning("  No waterbody data — waterbody_coverage set to NaN")
        query_gdf = query_gdf.copy()
        query_gdf["waterbody_coverage_500m"] = np.nan
        return query_gdf

    log.info(f"  Computing waterbody coverage (r={radius_m}m) for {len(query_gdf)} points...")

    q_proj = query_gdf.to_crs(crs_metres)
    wb_proj = waterbody_gdf.to_crs(crs_metres)
    wb_union = wb_proj.geometry.union_all() if hasattr(wb_proj.geometry, "union_all") else wb_proj.geometry.unary_union

    buffer_area = math.pi * radius_m**2

    coverages = q_proj.geometry.apply(
        lambda pt: pt.buffer(radius_m).intersection(wb_union).area / buffer_area
    )
    query_gdf = query_gdf.copy()
    query_gdf["waterbody_coverage_500m"] = coverages.values.astype(np.float32)
    log.info(f"  waterbody_coverage_500m: mean={coverages.mean():.4f}, max={coverages.max():.4f}")
    return query_gdf


def run_hydrology_pipeline(sample_only=False):
    """
    Full hydrology proximity pipeline.

    Parameters
    ----------
    sample_only : bool
        If True, uses only a 3×3 grid of query points for testing.
    """
    log.info("=" * 60)
    log.info("PHASE 3 — Hydrology Pipeline")
    log.info("=" * 60)

    # Define buffered bbox for loading (slightly larger than AOI)
    minx, miny, maxx, maxy = AOI_BOUNDS
    load_bbox = (
        minx - AOI_BUFFER_DEG,
        miny - AOI_BUFFER_DEG,
        maxx + AOI_BUFFER_DEG,
        maxy + AOI_BUFFER_DEG,
    )
    log.info(f"AOI: {AOI_BOUNDS}")
    log.info(f"Load bbox (with buffer): {load_bbox}")

    # Create query grid
    grid_spacing = 0.05 if sample_only else 0.005  # 0.05° for test, 0.005° (~500m) for full
    query_gdf = make_aoi_grid(AOI_BOUNDS, grid_spacing_deg=grid_spacing)
    log.info(f"Query grid: {len(query_gdf)} points (spacing={grid_spacing}°)")

    results = query_gdf.copy()

    # ── 1) Waterbodies ────────────────────────────────────────────────────────
    log.info("\n--- Processing: India Surface Waterbodies ---")
    wb_gdf = load_geojson_bbox_safe(WATERBODY_PATH, load_bbox, label="Waterbodies (5.07 GB)")

    if wb_gdf is not None and len(wb_gdf) > 0:
        log.info(f"  Waterbodies loaded: {len(wb_gdf)} features, CRS: {wb_gdf.crs}")
        results = compute_distance_to_nearest(results, wb_gdf, "dist_waterbody_m")
        results = compute_waterbody_coverage(results, wb_gdf, radius_m=500)
    else:
        log.warning("  Waterbody data not available for AOI — setting columns to NaN")
        results["dist_waterbody_m"] = np.nan
        results["waterbody_coverage_500m"] = np.nan

    # ── 2) River Network ──────────────────────────────────────────────────────
    log.info("\n--- Processing: River Network ---")
    river_gdf = load_geojson_bbox_safe(RIVER_PATH, load_bbox, label="Rivers (356 MB)")

    if river_gdf is not None and len(river_gdf) > 0:
        log.info(f"  Rivers loaded: {len(river_gdf)} features, CRS: {river_gdf.crs}")
        results = compute_distance_to_nearest(results, river_gdf, "dist_river_m")
    else:
        log.warning("  River data not available for AOI — setting dist_river_m to NaN")
        results["dist_river_m"] = np.nan

    # ── 3) Canal Network ──────────────────────────────────────────────────────
    log.info("\n--- Processing: Canal Network ---")
    canal_gdf = load_geojson_bbox_safe(CANAL_PATH, load_bbox, label="Canals (233 MB)")

    if canal_gdf is not None and len(canal_gdf) > 0:
        log.info(f"  Canals loaded: {len(canal_gdf)} features, CRS: {canal_gdf.crs}")
        results = compute_distance_to_nearest(results, canal_gdf, "dist_canal_m")
    else:
        log.warning("  Canal data not available for AOI — setting dist_canal_m to NaN")
        results["dist_canal_m"] = np.nan

    # ── 4) Basin membership ───────────────────────────────────────────────────
    log.info("\n--- Processing: River Basins ---")
    try:
        basin_gdf = gpd.read_file(BASIN_PATH)
        if basin_gdf.crs is None:
            basin_gdf = basin_gdf.set_crs("EPSG:4326")
        elif basin_gdf.crs.to_epsg() != 4326:
            basin_gdf = basin_gdf.to_crs("EPSG:4326")

        # Spatial join to get basin name for each query point
        joined = gpd.sjoin(
            results[["geometry", "lat", "lon"]],
            basin_gdf,
            how="left",
            predicate="within"
        )
        # Take first match for each point
        joined = joined.groupby(level=0).first()
        basin_col = next((c for c in basin_gdf.columns if "name" in c.lower() or "basin" in c.lower()), None)
        if basin_col and basin_col in joined.columns:
            results["basin_name"] = joined[basin_col].values
            log.info(f"  Basin join complete. Column used: {basin_col}")
            log.info(f"  Basins found: {results['basin_name'].dropna().unique()[:5]}")
        else:
            log.warning(f"  Basin name column not found. Available: {list(basin_gdf.columns)}")
            results["basin_name"] = None
    except Exception as e:
        log.warning(f"  Basin processing failed: {e}")
        results["basin_name"] = None

    # ── Final output ──────────────────────────────────────────────────────────
    results_out = results.drop(columns=["geometry"], errors="ignore")
    out_path = os.path.join(FEATURES_DIR, "hydrology_features_aoi.parquet")
    results_out.to_parquet(out_path, index=False)
    log.info(f"\nSaved: {out_path} ({os.path.getsize(out_path)/1e6:.3f} MB)")
    log.info(f"Shape: {results_out.shape}")
    log.info(f"Columns: {list(results_out.columns)}")
    log.info("\nSummary statistics:")
    log.info(results_out.describe().to_string())

    log.info("=" * 60)
    log.info("Hydrology pipeline complete.")
    return results_out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hydrology Proximity Pipeline")
    parser.add_argument("--sample", action="store_true", help="Run on sample grid for testing")
    args = parser.parse_args()
    run_hydrology_pipeline(sample_only=args.sample)
