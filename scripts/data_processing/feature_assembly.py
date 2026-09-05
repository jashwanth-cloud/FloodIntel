"""
Phase 3 — Step 6: Feature Dataset Assembly
===========================================
Assembles all computed environmental features into a single clean,
ML-ready feature dataset.

Available feature sources (from completed pipeline steps):
  - Sentinel-1 derived features (from training CSV / normalized TIF)
  - IMD rainfall features (daily, rolling, historical stats)
  - DEM features (elevation, slope) — only test tile available
  - Hydrology features (waterbody proximity, river proximity)
  - Admin/ward features — NOT available (boundaries missing)

Strategy:
  The flood AOI is a 512×512 raster at EPSG:4326.
  We create a per-pixel feature DataFrame for the AOI, joining:
    1. Sentinel-1 features per pixel (from normalized TIF)
    2. Nearest IMD rainfall grid cell values for the AOI date (2021-10)
    3. DEM features (NaN — no matching DEM tile)
    4. Hydrology proximity (from hydrology pipeline output)

Output:
  data/features/flood_features.parquet

Schema design:
  lat, lon                         — geographic identifiers
  date                             — observation date (from satellite pair)
  pixel_row, pixel_col             — raster pixel coordinates

  Sentinel-1 features (11 bands):
    before_vv, before_vh, after_vv, after_vh
    vv_change, vh_change, vv_ratio, vh_ratio
    before_vv_vh_ratio, after_vv_vh_ratio, vv_vh_change

  flood_label                      — ground truth (0/1)

  Rainfall features (nearest IMD grid cell):
    rainfall_1d, rainfall_3d, rainfall_7d, rainfall_mean_annual

  DEM features (NaN for AOI — no matching tile):
    elevation_m, slope_deg

  Hydrology features (from hydrology pipeline):
    dist_waterbody_m, waterbody_coverage_500m
    dist_river_m, dist_canal_m

  Admin features (NaN — boundaries missing):
    ward_id, district_id, state_id
"""

import os
import sys
import logging
import warnings
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy as rasterio_xy
from scipy.spatial import KDTree

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("feature_assembly")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
os.makedirs(FEATURES_DIR, exist_ok=True)

# AOI observation date (inferred from satellite pair metadata)
AOI_DATE = "2021-10-06"  # from selected_flood_pair.csv (after scene)

SENTINEL1_FEATURES = [
    "before_vv", "before_vh", "after_vv", "after_vh",
    "vv_change", "vh_change", "vv_ratio", "vh_ratio",
    "before_vv_vh_ratio", "after_vv_vh_ratio", "vv_vh_change",
]


def load_sentinel1_features():
    """
    Load the 11-band normalized Sentinel-1 feature raster and convert to DataFrame.
    Each row = one pixel with lat/lon and 11 band values.
    """
    log.info("Loading Sentinel-1 normalized features...")
    tif_path = os.path.join(PROC_DIR, "satellite_features_normalized.tif")

    with rasterio.open(tif_path) as src:
        crs = src.crs
        transform = src.transform
        width = src.width
        height = src.height
        bands = src.count
        nodata = src.nodata

        log.info(f"  TIF: {height}×{width} pixels, {bands} bands, CRS={crs}")
        data = src.read()  # (11, 512, 512)

    # Create pixel coordinate grid
    rows, cols = np.mgrid[0:height, 0:width]
    lons, lats = rasterio_xy(transform, rows.ravel(), cols.ravel())
    lons = np.array(lons, dtype=np.float32)
    lats = np.array(lats, dtype=np.float32)

    # Build DataFrame
    df = pd.DataFrame({
        "pixel_row": rows.ravel().astype(np.int32),
        "pixel_col": cols.ravel().astype(np.int32),
        "lat": lats,
        "lon": lons,
    })

    # Add 11 bands
    for i, feat_name in enumerate(SENTINEL1_FEATURES):
        band_data = data[i].ravel().astype(np.float32)
        if nodata is not None:
            band_data[band_data == nodata] = np.nan
        df[feat_name] = band_data

    log.info(f"  Sentinel-1 features: {df.shape}")
    return df


def load_flood_labels():
    """Load the flood prediction raster as ground-truth labels."""
    log.info("Loading flood labels...")
    label_path = os.path.join(PROC_DIR, "gfm_flood_reference.tif")
    if not os.path.exists(label_path):
        log.warning(f"  Label file not found: {label_path}")
        return None

    with rasterio.open(label_path) as src:
        labels = src.read(1).ravel().astype(np.int8)
        nodata = src.nodata

    if nodata is not None:
        labels = np.where(labels == nodata, -1, labels)

    log.info(f"  Labels: {np.unique(labels, return_counts=True)}")
    return labels


def join_rainfall_to_pixels(pixel_df, rainfall_dir, target_date):
    """
    Join nearest IMD grid cell rainfall to each pixel.

    Uses the rainfall daily data and computes:
      - rainfall_1d (day of), rainfall_3d, rainfall_7d
      - rainfall_mean_annual

    Uses KDTree for fast nearest-neighbor lookup.
    """
    log.info(f"Joining rainfall features for date: {target_date}...")

    # Try to load daily parquet
    daily_path = os.path.join(FEATURES_DIR, "rainfall_daily.parquet")
    stats_path = os.path.join(FEATURES_DIR, "rainfall_historical_stats.parquet")

    result_df = pixel_df.copy()

    if not os.path.exists(daily_path):
        log.warning("  Rainfall daily parquet not found — rainfall features will be NaN")
        result_df["rainfall_1d"] = np.nan
        result_df["rainfall_3d"] = np.nan
        result_df["rainfall_7d"] = np.nan
        result_df["rainfall_mean_annual"] = np.nan
        return result_df

    try:
        target_dt = pd.Timestamp(target_date)
        daily_df = pd.read_parquet(daily_path)
        daily_df["date"] = pd.to_datetime(daily_df["date"])

        # Get grid cells
        grid_cells = daily_df[["lat", "lon"]].drop_duplicates().values  # (N_cells, 2)
        tree = KDTree(grid_cells)

        # Query points: pixel lat/lon
        pixel_coords = pixel_df[["lat", "lon"]].values
        _, idx = tree.query(pixel_coords)

        # Get matched grid coordinates
        matched_lats = grid_cells[idx, 0]
        matched_lons = grid_cells[idx, 1]

        # Window of dates for rolling aggregation
        date_start = target_dt - pd.Timedelta(days=6)
        date_end = target_dt

        window_df = daily_df[
            (daily_df["date"] >= date_start) &
            (daily_df["date"] <= date_end)
        ].copy()

        # Create a pivot indexed by (lat, lon) → date → rainfall
        pivot = window_df.pivot_table(
            index=["lat", "lon"], columns="date", values="rainfall_mm"
        )

        dates_in_window = sorted(pivot.columns)
        n_available = len(dates_in_window)
        log.info(f"  Dates in rainfall window: {n_available} (from {date_start.date()} to {date_end.date()})")

        # Look up rainfall for matched grid cells
        def get_rain_window(lat, lon, n_days):
            """Sum last n_days of rainfall for a grid cell."""
            key = (round(lat, 4), round(lon, 4))
            if key not in pivot.index:
                return np.nan
            row = pivot.loc[key]
            valid_cols = [c for c in dates_in_window[-n_days:] if c in row.index]
            vals = row[valid_cols].dropna()
            return float(vals.sum()) if len(vals) > 0 else np.nan

        rain_1d = np.array([get_rain_window(lat, lon, 1)
                             for lat, lon in zip(matched_lats, matched_lons)], dtype=np.float32)
        rain_3d = np.array([get_rain_window(lat, lon, 3)
                             for lat, lon in zip(matched_lats, matched_lons)], dtype=np.float32)
        rain_7d = np.array([get_rain_window(lat, lon, 7)
                             for lat, lon in zip(matched_lats, matched_lons)], dtype=np.float32)

        result_df["rainfall_1d"] = rain_1d
        result_df["rainfall_3d"] = rain_3d
        result_df["rainfall_7d"] = rain_7d

        log.info(f"  rainfall_1d: mean={np.nanmean(rain_1d):.2f} mm, max={np.nanmax(rain_1d):.2f} mm")
        log.info(f"  rainfall_3d: mean={np.nanmean(rain_3d):.2f} mm")
        log.info(f"  rainfall_7d: mean={np.nanmean(rain_7d):.2f} mm")

    except Exception as e:
        log.warning(f"  Rainfall join failed: {e}")
        result_df["rainfall_1d"] = np.nan
        result_df["rainfall_3d"] = np.nan
        result_df["rainfall_7d"] = np.nan

    # Historical stats
    if os.path.exists(stats_path):
        try:
            stats_df = pd.read_parquet(stats_path)
            stats_cells = stats_df[["lat", "lon"]].values
            tree2 = KDTree(stats_cells)
            pixel_coords = pixel_df[["lat", "lon"]].values
            _, idx2 = tree2.query(pixel_coords)
            result_df["rainfall_mean_annual"] = stats_df["rainfall_mean_annual"].values[idx2].astype(np.float32)
            log.info(f"  rainfall_mean_annual: mean={result_df['rainfall_mean_annual'].mean():.2f} mm")
        except Exception as e:
            log.warning(f"  Historical stats join failed: {e}")
            result_df["rainfall_mean_annual"] = np.nan
    else:
        result_df["rainfall_mean_annual"] = np.nan

    return result_df


def join_hydrology_to_pixels(pixel_df):
    """Join hydrology proximity features to pixel DataFrame."""
    log.info("Joining hydrology features...")

    hydro_path = os.path.join(FEATURES_DIR, "hydrology_features_aoi.parquet")
    result_df = pixel_df.copy()

    hydro_cols = ["dist_waterbody_m", "waterbody_coverage_500m", "dist_river_m", "dist_canal_m"]

    if not os.path.exists(hydro_path):
        log.warning("  Hydrology features not found — setting to NaN")
        for col in hydro_cols:
            result_df[col] = np.nan
        return result_df

    try:
        hydro_df = pd.read_parquet(hydro_path)
        hydro_df = hydro_df.dropna(subset=["lat", "lon"])

        if len(hydro_df) == 0:
            log.warning("  Hydrology features DataFrame is empty")
            for col in hydro_cols:
                result_df[col] = np.nan
            return result_df

        hydro_coords = hydro_df[["lat", "lon"]].values
        tree = KDTree(hydro_coords)
        pixel_coords = pixel_df[["lat", "lon"]].values
        _, idx = tree.query(pixel_coords)

        for col in hydro_cols:
            if col in hydro_df.columns:
                result_df[col] = hydro_df[col].values[idx].astype(np.float32)
                log.info(f"  {col}: mean={result_df[col].mean():.1f}")
            else:
                result_df[col] = np.nan

    except Exception as e:
        log.warning(f"  Hydrology join failed: {e}")
        for col in hydro_cols:
            result_df[col] = np.nan

    return result_df


def assemble_feature_dataset(sample_only=False):
    """
    Assemble the full ML-ready feature dataset.
    """
    log.info("=" * 60)
    log.info("PHASE 3 — Feature Dataset Assembly")
    log.info("=" * 60)

    # ── Step 1: Sentinel-1 base ──────────────────────────────────────────────
    df = load_sentinel1_features()

    if sample_only:
        # Use first 1000 pixels for testing
        df = df.head(1000).copy()
        log.info(f"Sample mode: using {len(df)} pixels")

    # ── Step 2: Flood labels ──────────────────────────────────────────────────
    labels = load_flood_labels()
    if labels is not None:
        if sample_only:
            df["flood_label"] = labels[:len(df)]
        else:
            df["flood_label"] = labels
    else:
        df["flood_label"] = np.nan

    # ── Step 3: Date field ────────────────────────────────────────────────────
    df["date"] = pd.Timestamp(AOI_DATE)

    # ── Step 4: Rainfall join ─────────────────────────────────────────────────
    df = join_rainfall_to_pixels(df, FEATURES_DIR, AOI_DATE)

    # ── Step 5: DEM features ──────────────────────────────────────────────────
    # DEM test tile does not overlap AOI — mark as NaN and document
    log.info("DEM features: NaN (no matching DEM tile for AOI — see docs/dem_limitation_note.txt)")
    df["elevation_m"] = np.nan
    df["slope_deg"] = np.nan

    # ── Step 6: Hydrology join ────────────────────────────────────────────────
    df = join_hydrology_to_pixels(df)

    # ── Step 7: Admin features (missing — see docs/WARD_BOUNDARIES_MISSING.md)
    log.info("Admin features: NaN (ward boundaries not available)")
    df["ward_id"] = None
    df["district_id"] = None
    df["state_id"] = None

    # ── Step 8: Final column ordering ────────────────────────────────────────
    col_order = [
        # Identifiers
        "pixel_row", "pixel_col", "lat", "lon", "date",
        "ward_id", "district_id", "state_id",
        # Sentinel-1
        *SENTINEL1_FEATURES,
        "flood_label",
        # Rainfall
        "rainfall_1d", "rainfall_3d", "rainfall_7d", "rainfall_mean_annual",
        # DEM
        "elevation_m", "slope_deg",
        # Hydrology
        "dist_waterbody_m", "waterbody_coverage_500m", "dist_river_m", "dist_canal_m",
    ]
    # Keep only existing columns
    col_order = [c for c in col_order if c in df.columns]
    df = df[col_order]

    log.info(f"\nFinal feature dataset shape: {df.shape}")
    log.info(f"Columns ({len(df.columns)}): {list(df.columns)}")

    # Missing value summary
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    log.info("\nMissing value summary:")
    for col in df.columns:
        pct = missing_pct[col]
        if pct > 0:
            log.info(f"  {col}: {missing[col]:,} ({pct:.2f}%)")

    # Save output
    out_path = os.path.join(FEATURES_DIR, "flood_features.parquet")
    df.to_parquet(out_path, index=False)
    log.info(f"\nSaved: {out_path} ({os.path.getsize(out_path)/1e6:.2f} MB)")

    log.info("=" * 60)
    log.info("Feature assembly complete.")
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Feature Dataset Assembly")
    parser.add_argument("--sample", action="store_true", help="Assemble only 1000-pixel sample")
    args = parser.parse_args()
    assemble_feature_dataset(sample_only=args.sample)
