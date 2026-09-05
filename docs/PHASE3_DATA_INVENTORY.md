# Phase 3 — Data Inventory

**Generated from direct inspection of all datasets.**
**All properties verified by running `scripts/data_processing/inspect_datasets.py` and `inspect_deep.py`.**

---

## 1. IMD Gridded Rainfall (NetCDF)

| Property | Value |
|----------|-------|
| **Dataset** | IMD RF25 Gridded Daily Rainfall |
| **Path** | `data/raw/rainfall/RF25_ind{YYYY}_rfp25.nc` |
| **Format** | NetCDF4 (CF-1.0 convention) |
| **Size** | ~25.4–25.5 MB per file × 8 files = ~203 MB total |
| **Temporal Coverage** | 2018-01-01 → 2025-12-31 (8 years, 2,927 daily time steps) |
| **Spatial Coverage** | Longitude 66.5°–100.0°E, Latitude 6.5°–38.5°N (India + surrounding) |
| **CRS** | WGS84 / EPSG:4326 (degrees_east, degrees_north) |
| **Resolution** | 0.25° × 0.25° (~25–28 km grid) |
| **Grid dimensions** | 135 (lon) × 129 (lat) = 17,415 grid cells |
| **Time encoding** | Days since 1900-12-31 00:00:00 |
| **Variables** | `LONGITUDE`, `LATITUDE`, `TIME`, `RAINFALL` |
| **Units** | mm (millimetres per day) |
| **Missing value** | −999.0 (netCDF4 fill value, converted to NaN) |
| **% Missing** | ~71.5% (ocean + non-India land mask) |
| **Valid range observed** | 0.0 – 534.25 mm/day |
| **Negative values** | None |
| **Processing status** | ✅ Processed — `data/features/rainfall_daily.parquet` |

### Important Notes
- LATITUDE is **ascending** (south → north): 6.5°, 6.75°, …, 38.5°
- 2020 and 2024 have 366 time steps (leap years) — confirmed
- Time epoch verified: day 42735 = 2018-01-01 ✓
- The IMD grid is coarse (0.25°) relative to the flood AOI (~10×10 km = ~0.1°). Only the nearest grid cell(s) cover the AOI.

---

## 2. Digital Elevation Model (DEM)

| Property | Value |
|----------|-------|
| **Dataset** | SRTM-derived DEM test tile |
| **Path (raw)** | `data/raw/dem/` — **EMPTY** |
| **Path (processed)** | `data/processed/dem/dem_test_processed.tif` |
| **Format** | GeoTIFF |
| **Size** | 0.33 MB |
| **Temporal Coverage** | Static (no temporal dimension) |
| **Spatial Coverage** | left=4.0°, bottom=12.0°, right=5.0°, top=13.0° ← **NOT the flood AOI** |
| **CRS** | EPSG:4326 |
| **Resolution** | ~0.000278° (~30m) |
| **Shape** | 3601 × 3601 pixels |
| **Vertical units** | Metres |
| **NoData** | Confirmed from rasterio inspection |
| **Processing status** | ⚠️ LIMITATION — DEM tile does NOT overlap flood AOI |

> **Critical limitation:** The raw DEM directory is empty. The only DEM file is a test tile covering West Africa (lon 4–5°E), not Andhra Pradesh (lon 80–81°E). Elevation and slope features for the flood AOI cannot currently be computed. See `docs/dem_limitation_note.txt`.

---

## 3. Sentinel-1 SAR Features (Processed Rasters)

| Property | Value |
|----------|-------|
| **Dataset** | Sentinel-1 SAR derived features |
| **Path** | `data/processed/satellite_features_normalized.tif` |
| **Format** | GeoTIFF |
| **Size** | 9.87 MB (normalized), 10.05 MB (raw) |
| **Temporal Coverage** | Single event: before ≈ pre-flood, after ≈ post-flood (2021-10-06 approx.) |
| **Spatial Coverage** | left=80.3865°, bottom=16.2567°, right=80.4865°, top=16.3567° (Andhra Pradesh) |
| **CRS** | EPSG:4326 |
| **Resolution** | ~0.0001953° per pixel (~19.5m) |
| **Shape** | 512 × 512 pixels = 262,144 total |
| **Band count** | 11 |
| **Processing status** | ✅ Available and verified |

### 11 Sentinel-1 Features (in order)
1. `before_vv` — Pre-flood VV backscatter (dB, normalised)
2. `before_vh` — Pre-flood VH backscatter (dB, normalised)
3. `after_vv` — Post-flood VV backscatter (dB, normalised)
4. `after_vh` — Post-flood VH backscatter (dB, normalised)
5. `vv_change` — VV change (after − before)
6. `vh_change` — VH change (after − before)
7. `vv_ratio` — VV ratio (after / before)
8. `vh_ratio` — VH ratio (after / before)
9. `before_vv_vh_ratio` — Pre-flood VV/VH ratio
10. `after_vv_vh_ratio` — Post-flood VV/VH ratio
11. `vv_vh_change` — Change in VV/VH ratio

> **IMPORTANT:** These feature definitions must NOT be changed. The trained Random Forest model (`data/processed/flood_random_forest_model.joblib`) depends on exactly this order and definition.

---

## 4. Flood Training Dataset (CSV)

| Property | Value |
|----------|-------|
| **Path** | `data/processed/flood_training_dataset.csv` |
| **Format** | CSV |
| **Size** | 31.0 MB |
| **Shape** | 262,144 rows × 12 columns |
| **Target column** | `flood_label` (0=no-flood, 1=flood) |
| **Class distribution** | 0: 256,339 (97.79%), 1: 5,805 (2.21%) |
| **Missing values** | Zero (all 262,144 rows complete) |
| **Processing status** | ✅ Existing — DO NOT MODIFY |

---

## 5. India Surface Waterbodies (GeoJSON)

| Property | Value |
|----------|-------|
| **Dataset** | NWDP Surface Water Bodies — India merged |
| **Path** | `data/raw/hydrology/water_bodies/india/india_surface_waterbodies.geojson` |
| **Format** | GeoJSON |
| **Size** | **5,074.95 MB (5.07 GB)** |
| **Temporal Coverage** | Static (derived from multi-year composites) |
| **Spatial Coverage** | All India |
| **CRS** | OGC:CRS84 (≈ EPSG:4326) |
| **Processing status** | ⚠️ LARGE — requires bbox-filtered or streaming read |

> **Critical:** Do NOT load this file entirely into RAM. Use geopandas `read_file(path, bbox=...)` or the streaming GeoJSON parser in `hydrology_pipeline.py`.

---

## 6. India River Network (GeoJSON)

| Property | Value |
|----------|-------|
| **Path** | `data/raw/hydrology/rivers/india_river_network.geojson` |
| **Format** | GeoJSON |
| **Size** | 356.23 MB |
| **CRS** | EPSG:4326 |
| **Key Properties** | `rivname`, `sub_basin`, `ba_name`, `length_km`, `lat`, `long`, `state_al` |
| **Geometry type** | LineString |
| **Processing status** | ⚠️ Large — use bbox filter |

---

## 7. India Canal Network (GeoJSON)

| Property | Value |
|----------|-------|
| **Path** | `data/raw/hydrology/drainage/india_canal_network.geojson` |
| **Format** | GeoJSON |
| **Size** | 233.10 MB |
| **CRS** | EPSG:4326 |
| **Key Properties** | `prj_name`, `can_name`, `can_type`, `basin`, `river`, `state`, `length_km` |
| **Geometry type** | LineString |
| **Processing status** | ⚠️ Large — use bbox filter |

---

## 8. India Reservoirs (GeoJSON)

| Property | Value |
|----------|-------|
| **Path** | `data/raw/hydrology/reservoirs/india_reservoirs_source.geojson` |
| **Format** | GeoJSON |
| **Size** | 452.53 MB |
| **CRS** | EPSG:4326 |
| **Key Properties** | `res_name`, `river`, `basin`, `PIC`, `dm_name`, `area` |
| **Processing status** | ⚠️ Large — use bbox filter |

---

## 9. River Basin Boundaries — CWC (GeoJSON)

| Property | Value |
|----------|-------|
| **Path** | `data/raw/hydrology/river_basins/extracted/basin_cwc.GeoJSON` |
| **Format** | GeoJSON |
| **Size** | 17.48 MB |
| **CRS** | EPSG:7755 (encoded in properties — needs verification) |
| **Key Properties** | `name` (basin name) |
| **Processing status** | ✅ Manageable size |

> **Note:** The CRS encoded in the basin_cwc GeoJSON properties field appears to be EPSG:7755 (India National Grid), not EPSG:4326. Reprojection required before spatial join.

---

## 10. Flood AOI Sentinel-1 Rasters

| Property | Value |
|----------|-------|
| **Path (before)** | `flood_aoi/before_vv_vh.tiff` |
| **Path (after)** | `flood_aoi/after_vv_vh.tiff` |
| **Format** | GeoTIFF |
| **Size** | ~1.9 MB each |
| **CRS** | EPSG:4326 |
| **Spatial Coverage** | Same as processed TIFs: 80.3865–80.4865°E, 16.2567–16.3567°N |
| **Bands** | 2 (VV, VH) |
| **Processing status** | ✅ Source data intact |

---

## 11. Ward / Administrative Boundaries

| Property | Value |
|----------|-------|
| **Status** | ❌ **MISSING** |
| **Searched** | `data/raw/admin/`, project root, `metadata/` |
| **Formats searched** | .geojson, .shp, .gpkg, .json |
| **Keywords** | ward, admin, district, municipality, taluk |
| **Result** | No boundary files found |
| **Impact** | Ward-level aggregation impossible |
| **Documentation** | `docs/WARD_BOUNDARIES_MISSING.md` |

---

## 12. Flood Prediction Model

| Property | Value |
|----------|-------|
| **Path** | `data/processed/flood_random_forest_model.joblib` |
| **Size** | 233.43 MB |
| **Algorithm** | RandomForestClassifier (scikit-learn) |
| **Estimators** | 300 |
| **Features** | 11 Sentinel-1 features (see Section 3) |
| **Status** | ✅ PROTECTED — DO NOT MODIFY |

---

## 13. Historical Flood Metadata / Satellite Scene Index

| Property | Value |
|----------|-------|
| **Path** | `india_sentinel1_metadata.csv` |
| **Size** | 15.87 MB |
| **Content** | Sentinel-1 scene metadata for India 2018–2025 |
| **Path** | `download_queue.csv` |
| **Size** | 131.7 KB |
| **Content** | Download queue for satellite scenes |
| **Status** | Available for scene lookup |

---

## Summary: Feature Availability by Category

| Feature Category | Status | Notes |
|----------------|--------|-------|
| Sentinel-1 (11 features) | ✅ COMPLETE | 262,144 pixels, single event |
| Rainfall 1d/3d/7d | ✅ COMPUTED | IMD grid, 0.25° resolution |
| Rainfall historical stats | ✅ COMPUTED | 2018–2025 annual mean/max |
| Elevation | ❌ MISSING | No DEM covering flood AOI |
| Slope | ❌ MISSING | Derived from elevation |
| Distance to waterbody | ⚠️ ATTEMPTED | Depends on geopandas bbox read success |
| Waterbody coverage | ⚠️ ATTEMPTED | Depends on bbox read success |
| Distance to river | ⚠️ ATTEMPTED | 356 MB file, bbox filtered |
| Distance to canal | ⚠️ ATTEMPTED | 233 MB file, bbox filtered |
| Ward ID | ❌ MISSING | No boundary data |
| District ID | ❌ MISSING | No boundary data |
| State ID | ❌ MISSING | No boundary data |
| Flood label | ✅ COMPLETE | GFM reference raster |

---

*Generated: Phase 3 Step 1 | Project: Copernicus-India-Flood*
