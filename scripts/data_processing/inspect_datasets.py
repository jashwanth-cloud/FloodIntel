"""
Phase 3 — Step 1: Dataset Inspection Script
Inspects all available datasets and writes findings to a JSON report.
Does NOT modify any data.
"""

import os
import sys
import json
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_PATH = os.path.join(BASE_DIR, "docs", "phase3_dataset_inspection.json")

report = {}

# ─────────────────────────────────────────────────────────────────────────────
# 1) IMD Rainfall NetCDF
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: IMD Rainfall NetCDF files")
print("="*60)

rainfall_dir = os.path.join(BASE_DIR, "data", "raw", "rainfall")
nc_files = sorted([f for f in os.listdir(rainfall_dir) if f.endswith(".nc")])
print(f"Found {len(nc_files)} NetCDF files: {nc_files}")

rainfall_info = {"files": [], "error": None}

try:
    import netCDF4 as nc4
    import numpy as np

    for fname in nc_files:
        fpath = os.path.join(rainfall_dir, fname)
        fsize = os.path.getsize(fpath)
        ds = nc4.Dataset(fpath, "r")

        file_info = {
            "filename": fname,
            "size_mb": round(fsize / 1e6, 2),
            "dimensions": {k: len(v) for k, v in ds.dimensions.items()},
            "variables": {}
        }

        for vname, var in ds.variables.items():
            vinfo = {
                "shape": list(var.shape),
                "dtype": str(var.dtype),
                "units": getattr(var, "units", "N/A"),
                "long_name": getattr(var, "long_name", "N/A"),
                "missing_value": float(getattr(var, "missing_value", float("nan"))) if hasattr(var, "missing_value") else None,
                "fill_value": float(getattr(var, "_FillValue", float("nan"))) if hasattr(var, "_FillValue") else None,
            }
            # Sample values for coordinate/data variables
            try:
                arr = var[:]
                valid_mask = ~np.ma.getmaskarray(arr)
                valid = arr[valid_mask]
                if len(valid) > 0:
                    vinfo["min"] = float(np.nanmin(valid))
                    vinfo["max"] = float(np.nanmax(valid))
                    vinfo["n_valid"] = int(valid_mask.sum())
                    vinfo["n_total"] = int(arr.size)
                    vinfo["pct_missing"] = round(100.0 * (1 - vinfo["n_valid"] / vinfo["n_total"]), 4)
            except Exception as e:
                vinfo["sample_error"] = str(e)

            file_info["variables"][vname] = vinfo

        ds.close()
        rainfall_info["files"].append(file_info)
        print(f"  {fname}: dims={file_info['dimensions']}, vars={list(file_info['variables'].keys())}")

except ImportError:
    rainfall_info["error"] = "netCDF4 not installed"
    print("  ERROR: netCDF4 not installed")
except Exception as e:
    rainfall_info["error"] = str(e)
    print(f"  ERROR: {e}")

report["rainfall_netcdf"] = rainfall_info

# ─────────────────────────────────────────────────────────────────────────────
# 2) DEM
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: DEM data")
print("="*60)

dem_raw_dir = os.path.join(BASE_DIR, "data", "raw", "dem")
dem_proc_dir = os.path.join(BASE_DIR, "data", "processed", "dem")
dem_info = {"raw_files": [], "processed_files": [], "raster_details": {}, "error": None}

for d, label in [(dem_raw_dir, "raw"), (dem_proc_dir, "processed")]:
    found = []
    for root, dirs, files in os.walk(d):
        for f in files:
            full = os.path.join(root, f)
            found.append({"path": full, "size_mb": round(os.path.getsize(full) / 1e6, 2)})
    dem_info[f"{label}_files"] = found
    print(f"  DEM {label}: {len(found)} files")
    for ff in found:
        print(f"    {ff['path']} ({ff['size_mb']} MB)")

# Try rasterio on the processed test file
try:
    import rasterio
    test_dem = os.path.join(dem_proc_dir, "dem_test_processed.tif")
    if os.path.exists(test_dem):
        with rasterio.open(test_dem) as src:
            data = src.read(1, masked=True)
            nodata = src.nodata
            dem_info["raster_details"] = {
                "path": test_dem,
                "crs": str(src.crs),
                "transform": list(src.transform),
                "width": src.width,
                "height": src.height,
                "count": src.count,
                "dtype": str(src.dtypes[0]),
                "nodata": float(nodata) if nodata is not None else None,
                "bounds": list(src.bounds),
                "resolution_deg": [abs(src.transform.a), abs(src.transform.e)],
                "min_elevation": float(data.min()) if data.count() > 0 else None,
                "max_elevation": float(data.max()) if data.count() > 0 else None,
                "n_valid_pixels": int((~data.mask).sum()) if hasattr(data, "mask") else int(data.size),
                "n_total_pixels": int(data.size),
            }
            print(f"  DEM processed TIF: CRS={src.crs}, bounds={src.bounds}, shape={src.height}x{src.width}")
except ImportError:
    dem_info["error"] = "rasterio not installed"
    print("  ERROR: rasterio not installed")
except Exception as e:
    dem_info["error"] = str(e)
    print(f"  ERROR: {e}")

report["dem"] = dem_info

# ─────────────────────────────────────────────────────────────────────────────
# 3) Existing satellite features TIFs
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: Processed satellite features TIFs")
print("="*60)

proc_dir = os.path.join(BASE_DIR, "data", "processed")
sat_tifs = [
    "satellite_features.tif",
    "satellite_features_normalized.tif",
    "flood_prediction.tif",
    "gfm_flood_reference.tif",
]
sat_info = {}

try:
    import rasterio
    for tif in sat_tifs:
        tpath = os.path.join(proc_dir, tif)
        if os.path.exists(tpath):
            with rasterio.open(tpath) as src:
                info = {
                    "path": tpath,
                    "size_mb": round(os.path.getsize(tpath) / 1e6, 2),
                    "crs": str(src.crs),
                    "bounds": list(src.bounds),
                    "width": src.width,
                    "height": src.height,
                    "bands": src.count,
                    "dtype": str(src.dtypes[0]),
                    "nodata": float(src.nodata) if src.nodata is not None else None,
                    "transform": list(src.transform),
                    "resolution_deg": [abs(src.transform.a), abs(src.transform.e)],
                }
                print(f"  {tif}: CRS={src.crs}, bands={src.count}, shape={src.height}x{src.width}, bounds={src.bounds}")
            sat_info[tif] = info
        else:
            sat_info[tif] = {"error": "file not found"}
            print(f"  {tif}: NOT FOUND")
except Exception as e:
    sat_info["error"] = str(e)
    print(f"  ERROR: {e}")

report["satellite_tifs"] = sat_info

# ─────────────────────────────────────────────────────────────────────────────
# 4) Hydrology GeoJSON — header only (no full load of large files)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: Hydrology GeoJSON (header/sample only)")
print("="*60)

hydro_files = {
    "river_network": os.path.join(BASE_DIR, "data", "raw", "hydrology", "rivers", "india_river_network.geojson"),
    "reservoirs": os.path.join(BASE_DIR, "data", "raw", "hydrology", "reservoirs", "india_reservoirs_source.geojson"),
    "canal_network": os.path.join(BASE_DIR, "data", "raw", "hydrology", "drainage", "india_canal_network.geojson"),
    "waterbodies_india": os.path.join(BASE_DIR, "data", "raw", "hydrology", "water_bodies", "india", "india_surface_waterbodies.geojson"),
    "river_basins_cwc": os.path.join(BASE_DIR, "data", "raw", "hydrology", "river_basins", "extracted", "basin_cwc.GeoJSON"),
}

hydro_info = {}

try:
    import fiona
    import fiona.errors

    for key, fpath in hydro_files.items():
        if not os.path.exists(fpath):
            hydro_info[key] = {"error": "file not found"}
            print(f"  {key}: NOT FOUND")
            continue

        fsize_mb = round(os.path.getsize(fpath) / 1e6, 2)
        info = {"path": fpath, "size_mb": fsize_mb}

        try:
            with fiona.open(fpath, "r") as src:
                info["crs"] = str(src.crs) if src.crs else "None"
                info["driver"] = src.driver
                info["feature_count"] = len(src)
                info["geometry_type"] = src.schema["geometry"]
                info["properties"] = list(src.schema["properties"].keys())

                # Bounds
                if src.bounds:
                    info["bounds"] = list(src.bounds)

                # Sample first feature's properties
                try:
                    first = next(iter(src))
                    info["sample_properties"] = {k: str(v) for k, v in first["properties"].items()}
                except StopIteration:
                    info["sample_properties"] = {}

            print(f"  {key}: {fsize_mb} MB, features={info.get('feature_count','?')}, geom={info.get('geometry_type','?')}, CRS={info.get('crs','?')}")
            print(f"    Properties: {info.get('properties','?')}")

        except Exception as e:
            info["error"] = str(e)
            print(f"  {key}: ERROR - {e}")

        hydro_info[key] = info

except ImportError:
    # Fall back to raw file header reading for size/structure
    print("  fiona not available, using raw file header approach")
    for key, fpath in hydro_files.items():
        if not os.path.exists(fpath):
            hydro_info[key] = {"error": "file not found"}
            continue
        fsize_mb = round(os.path.getsize(fpath) / 1e6, 2)
        # Read first 4KB to peek at schema
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                header = f.read(4096)
            hydro_info[key] = {"path": fpath, "size_mb": fsize_mb, "header_snippet": header[:500]}
            print(f"  {key}: {fsize_mb} MB (fiona not available, raw peek only)")
        except Exception as e:
            hydro_info[key] = {"path": fpath, "size_mb": fsize_mb, "error": str(e)}

report["hydrology_geojson"] = hydro_info

# ─────────────────────────────────────────────────────────────────────────────
# 5) Training CSV
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: Training dataset CSV")
print("="*60)

try:
    import pandas as pd
    csv_path = os.path.join(BASE_DIR, "data", "processed", "flood_training_dataset.csv")
    df = pd.read_csv(csv_path)
    train_info = {
        "path": csv_path,
        "size_mb": round(os.path.getsize(csv_path) / 1e6, 2),
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "missing_pct": {k: round(100.0 * v / len(df), 3) for k, v in df.isnull().sum().items() if v > 0},
        "class_distribution": df["label"].value_counts().to_dict() if "label" in df.columns else None,
        "numeric_stats": df.describe().to_dict(),
    }
    print(f"  Training CSV: {df.shape}, columns={list(df.columns)}")
    print(f"  Class distribution: {train_info['class_distribution']}")
except Exception as e:
    train_info = {"error": str(e)}
    print(f"  ERROR: {e}")

report["training_csv"] = train_info

# ─────────────────────────────────────────────────────────────────────────────
# 6) Administrative / ward boundaries
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: Administrative/ward boundaries")
print("="*60)

ward_search_dirs = [
    os.path.join(BASE_DIR, "data", "raw"),
    os.path.join(BASE_DIR, "data"),
    os.path.join(BASE_DIR, "metadata"),
    BASE_DIR,
]

ward_candidates = []
ward_extensions = (".geojson", ".shp", ".gpkg", ".json")
admin_keywords = ("ward", "admin", "district", "municipality", "taluk", "state", "boundary")

for sdir in ward_search_dirs:
    if not os.path.isdir(sdir):
        continue
    for root, dirs, files in os.walk(sdir):
        # skip venv and huge dirs
        dirs[:] = [d for d in dirs if d not in ("venv", "__pycache__", ".git", "node_modules")]
        for f in files:
            if any(f.lower().endswith(ext) for ext in ward_extensions):
                if any(kw in f.lower() for kw in admin_keywords):
                    ward_candidates.append(os.path.join(root, f))

report["admin_ward_boundaries"] = {
    "candidates_found": ward_candidates,
    "count": len(ward_candidates),
    "note": "Files found whose names contain ward/admin/district/municipality keywords"
}
print(f"  Admin boundary candidates: {ward_candidates}")

# ─────────────────────────────────────────────────────────────────────────────
# 7) Flood AOI TIFs
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("INSPECTING: Flood AOI TIFs")
print("="*60)

aoi_dir = os.path.join(BASE_DIR, "flood_aoi")
aoi_info = {}
try:
    import rasterio
    for fname in os.listdir(aoi_dir):
        if fname.endswith(".tiff") or fname.endswith(".tif"):
            fpath = os.path.join(aoi_dir, fname)
            with rasterio.open(fpath) as src:
                info = {
                    "crs": str(src.crs),
                    "bounds": list(src.bounds),
                    "width": src.width,
                    "height": src.height,
                    "bands": src.count,
                    "dtype": str(src.dtypes[0]),
                    "nodata": float(src.nodata) if src.nodata is not None else None,
                    "size_mb": round(os.path.getsize(fpath) / 1e6, 2),
                }
                print(f"  {fname}: CRS={src.crs}, bands={src.count}, bounds={src.bounds}")
            aoi_info[fname] = info
except Exception as e:
    aoi_info["error"] = str(e)
    print(f"  ERROR: {e}")

report["flood_aoi"] = aoi_info

# ─────────────────────────────────────────────────────────────────────────────
# 8) Write report
# ─────────────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, default=str)

print(f"\n{'='*60}")
print(f"Inspection report written to: {OUTPUT_PATH}")
print("="*60)
