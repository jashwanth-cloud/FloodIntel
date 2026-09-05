"""
Phase 3 — Step 2: IMD Rainfall Processing Pipeline
===================================================
Processes IMD gridded rainfall NetCDF files (RF25 daily, 0.25° resolution)
for 2018–2025 and produces temporal rainfall features.

Key properties confirmed by inspection:
  - Variables: LONGITUDE (135), LATITUDE (129), TIME (365/366), RAINFALL
  - Units: RAINFALL in mm, TIME in "days since 1900-12-31"
  - CRS: WGS84 (geographic, degrees)
  - LONGITUDE range: 66.5–100.0 °E
  - LATITUDE range: 6.5–38.5 °N
  - Missing value: -999.0 (encoded as NaN mask in netCDF4)
  - ~71.5% missing (ocean/outside-India land mask)
  - LATITUDE is ascending (south to north) — confirmed

Outputs:
  data/features/rainfall_grid_features.parquet   — per-grid-cell rainfall features
  data/features/rainfall_daily.parquet            — full daily grid (memory-mapped)
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import netCDF4 as nc4
from datetime import date, timedelta

# ── setup ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rainfall_pipeline")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAINFALL_DIR = os.path.join(BASE_DIR, "data", "raw", "rainfall")
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
os.makedirs(FEATURES_DIR, exist_ok=True)

NC_FILES = sorted([
    os.path.join(RAINFALL_DIR, f)
    for f in os.listdir(RAINFALL_DIR)
    if f.endswith(".nc")
])

# IMD time reference epoch: days since 1900-12-31
_EPOCH = date(1900, 12, 31)


def nc_time_to_dates(time_values):
    """Convert IMD time values (days since 1900-12-31) to list of date objects."""
    return [_EPOCH + timedelta(days=int(t)) for t in time_values]


def load_nc_metadata(nc_path):
    """Return grid metadata from a NetCDF file without loading RAINFALL data."""
    ds = nc4.Dataset(nc_path, "r")
    lons = ds.variables["LONGITUDE"][:].data.copy()  # (135,) 66.5..100.0
    lats = ds.variables["LATITUDE"][:].data.copy()   # (129,) 6.5..38.5
    times = ds.variables["TIME"][:].data.copy()
    ds.close()
    return lons, lats, times


def process_single_year(nc_path, sample_only=False):
    """
    Process one year's NetCDF file and return a DataFrame with columns:
      lat, lon, date, rainfall_mm

    If sample_only=True, returns only a single day slice for testing.

    Memory strategy:
    - Reads the entire year's RAINFALL cube at once (365×129×135 float32 ~= 24 MB).
    - Applies the missing-value mask (-999 fill).
    - Converts to a DataFrame only for valid (non-NaN) cells.
    """
    log.info(f"Processing: {os.path.basename(nc_path)}")

    ds = nc4.Dataset(nc_path, "r")
    lons = ds.variables["LONGITUDE"][:].data.copy()
    lats = ds.variables["LATITUDE"][:].data.copy()
    time_vals = ds.variables["TIME"][:].data.copy()
    rain_var = ds.variables["RAINFALL"]

    # Load full year
    rain = rain_var[:]  # masked array (TIME, LAT, LON)
    ds.close()

    # Convert masked → float with NaN
    if isinstance(rain, np.ma.MaskedArray):
        rain = rain.filled(np.nan)

    dates = nc_time_to_dates(time_vals)

    if sample_only:
        # Return only first day
        day_idx = 0
        rain_day = rain[day_idx]
        lat_idx, lon_idx = np.where(~np.isnan(rain_day))
        df = pd.DataFrame({
            "lat": lats[lat_idx],
            "lon": lons[lon_idx],
            "date": dates[day_idx],
            "rainfall_mm": rain_day[lat_idx, lon_idx].astype(np.float32),
        })
        return df, lons, lats, dates, rain

    # Build DataFrame for all valid pixels across all days
    n_times = len(dates)
    records = []
    for t in range(n_times):
        day_rain = rain[t]
        lat_idx, lon_idx = np.where(~np.isnan(day_rain))
        if len(lat_idx) == 0:
            continue
        df_day = pd.DataFrame({
            "lat": lats[lat_idx].astype(np.float32),
            "lon": lons[lon_idx].astype(np.float32),
            "date": dates[t],
            "rainfall_mm": day_rain[lat_idx, lon_idx].astype(np.float32),
        })
        records.append(df_day)

    if not records:
        return pd.DataFrame(), lons, lats, dates, rain

    df_year = pd.concat(records, ignore_index=True)
    df_year["date"] = pd.to_datetime(df_year["date"])
    return df_year, lons, lats, dates, rain


def compute_rolling_features(df_daily, windows=(1, 3, 7)):
    """
    Compute rolling rainfall features per grid cell.

    Input df_daily must have columns: lat, lon, date, rainfall_mm
    Output adds: rainfall_1d, rainfall_3d, rainfall_7d

    Strategy: pivot to (date × cell), compute rolling, then melt back.
    Only feasible for a limited number of cells; for India-wide (135×129=17415 cells)
    this is manageable (17415 × 365 = ~6.4M values, ~51 MB float32).
    """
    log.info("Computing rolling rainfall features...")

    # Create cell id
    df_daily = df_daily.copy()
    df_daily["cell_id"] = (df_daily["lat"].round(4).astype(str) + "_" +
                            df_daily["lon"].round(4).astype(str))
    df_daily = df_daily.sort_values(["cell_id", "date"])

    roll_frames = []
    cell_meta = df_daily[["cell_id", "lat", "lon"]].drop_duplicates("cell_id")

    # Pivot: date × cell
    pivot = df_daily.pivot_table(index="date", columns="cell_id", values="rainfall_mm", aggfunc="first")
    pivot = pivot.sort_index()

    results = {"date": pivot.index}
    for w in windows:
        rolled = pivot.rolling(window=w, min_periods=1).sum()
        results[f"rainfall_{w}d"] = rolled

    # Build output: for each (date, cell) → features
    roll_df_parts = []
    for w in windows:
        melted = results[f"rainfall_{w}d"].reset_index().melt(
            id_vars="date", var_name="cell_id", value_name=f"rainfall_{w}d"
        )
        roll_df_parts.append(melted.set_index(["date", "cell_id"]))

    roll_combined = pd.concat(roll_df_parts, axis=1).reset_index()
    roll_combined = roll_combined.merge(cell_meta, on="cell_id", how="left")

    return roll_combined


def compute_annual_stats(all_years_df):
    """Compute per-cell historical rainfall statistics from all years."""
    log.info("Computing annual/historical rainfall statistics...")

    cell_stats = (
        all_years_df
        .groupby(["lat", "lon"])["rainfall_mm"]
        .agg(
            rainfall_mean_annual="mean",
            rainfall_std_annual="std",
            rainfall_max_ever="max",
            rainfall_n_days="count",
        )
        .reset_index()
    )
    return cell_stats


def run_rainfall_pipeline(sample_only=False):
    """
    Full rainfall pipeline.

    Parameters
    ----------
    sample_only : bool
        If True, processes only the first file and first day (for testing).
    """
    log.info("=" * 60)
    log.info("PHASE 3 — Rainfall Pipeline")
    log.info(f"Files found: {len(NC_FILES)}")
    log.info(f"Sample-only mode: {sample_only}")
    log.info("=" * 60)

    all_dfs = []

    files_to_process = NC_FILES[:1] if sample_only else NC_FILES

    for nc_path in files_to_process:
        df_year, lons, lats, dates, rain = process_single_year(
            nc_path, sample_only=sample_only
        )
        if df_year.empty:
            log.warning(f"  No valid data in {nc_path}")
            continue
        log.info(f"  Year shape: {df_year.shape}, date range: {df_year['date'].min()} -> {df_year['date'].max()}")
        all_dfs.append(df_year)

    if not all_dfs:
        log.error("No rainfall data loaded. Aborting.")
        return

    all_rain_df = pd.concat(all_dfs, ignore_index=True)
    all_rain_df["date"] = pd.to_datetime(all_rain_df["date"])
    all_rain_df = all_rain_df.sort_values(["lat", "lon", "date"]).reset_index(drop=True)

    log.info(f"Total records: {len(all_rain_df):,}")
    log.info(f"Date range: {all_rain_df['date'].min()} -> {all_rain_df['date'].max()}")
    log.info(f"Grid cells: {all_rain_df[['lat', 'lon']].drop_duplicates().shape[0]:,}")
    log.info(f"Rainfall stats: min={all_rain_df['rainfall_mm'].min():.2f}, max={all_rain_df['rainfall_mm'].max():.2f}")

    # Validate: no impossible values
    neg_count = (all_rain_df["rainfall_mm"] < 0).sum()
    extreme_count = (all_rain_df["rainfall_mm"] > 600).sum()
    log.info(f"Validation — negative values: {neg_count}, extreme (>600mm): {extreme_count}")

    # Save daily output
    daily_out = os.path.join(FEATURES_DIR, "rainfall_daily.parquet")
    all_rain_df.to_parquet(daily_out, index=False)
    log.info(f"Saved: {daily_out} ({os.path.getsize(daily_out)/1e6:.2f} MB)")

    # Rolling features — skip for sample mode (only 1 day)
    if not sample_only and len(all_rain_df["date"].unique()) >= 7:
        roll_df = compute_rolling_features(all_rain_df, windows=(1, 3, 7))
        roll_out = os.path.join(FEATURES_DIR, "rainfall_rolling_features.parquet")
        roll_df.to_parquet(roll_out, index=False)
        log.info(f"Saved: {roll_out} ({os.path.getsize(roll_out)/1e6:.2f} MB)")
        log.info(f"Rolling features shape: {roll_df.shape}")
    else:
        log.info("Skipping rolling features (sample mode or insufficient days)")
        roll_df = all_rain_df.copy()

    # Historical stats
    stats_df = compute_annual_stats(all_rain_df)
    stats_out = os.path.join(FEATURES_DIR, "rainfall_historical_stats.parquet")
    stats_df.to_parquet(stats_out, index=False)
    log.info(f"Saved: {stats_out} ({os.path.getsize(stats_out)/1e6:.2f} MB)")
    log.info(f"Historical stats shape: {stats_df.shape}")

    log.info("=" * 60)
    log.info("Rainfall pipeline complete.")
    return all_rain_df, stats_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IMD Rainfall Processing Pipeline")
    parser.add_argument("--sample", action="store_true", help="Run on 1 day sample for testing")
    args = parser.parse_args()
    run_rainfall_pipeline(sample_only=args.sample)
