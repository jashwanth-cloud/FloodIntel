"""
Phase 3 — Step 1b: Deep NetCDF + GeoJSON header inspection
"""

import os
import json
import numpy as np
import netCDF4 as nc4

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
rainfall_dir = os.path.join(BASE_DIR, "data", "raw", "rainfall")

print("="*60)
print("DEEP NETCDF INSPECTION")
print("="*60)

nc_files = sorted([f for f in os.listdir(rainfall_dir) if f.endswith(".nc")])

# Inspect first file in full detail
first_file = nc_files[0]
fpath = os.path.join(rainfall_dir, first_file)
ds = nc4.Dataset(fpath, "r")

print(f"\nFile: {first_file}")
print(f"Global attributes: {list(ds.ncattrs())}")
for attr in ds.ncattrs():
    print(f"  {attr} = {getattr(ds, attr)}")

print(f"\nVariables detail:")
for vname, var in ds.variables.items():
    arr = var[:]
    print(f"\n  [{vname}]")
    print(f"    shape   : {arr.shape}")
    print(f"    dtype   : {var.dtype}")
    print(f"    units   : {getattr(var, 'units', 'N/A')}")
    print(f"    long_name: {getattr(var, 'long_name', 'N/A')}")
    if hasattr(var, 'missing_value'):
        print(f"    missing_value: {var.missing_value}")
    if hasattr(var, '_FillValue'):
        print(f"    _FillValue: {var._FillValue}")

    # Show actual values
    if vname in ['LONGITUDE', 'LATITUDE']:
        vals = arr[:]
        print(f"    values[0:5]: {vals[:5].tolist()}")
        print(f"    values[-5:]: {vals[-5:].tolist()}")
        print(f"    min={float(vals.min()):.4f}, max={float(vals.max()):.4f}, n={len(vals)}")
    elif vname == 'TIME':
        print(f"    values[0:5]: {arr[:5].tolist()}")
        print(f"    values[-5:]: {arr[-5:].tolist()}")
    elif vname == 'RAINFALL':
        valid = arr[~np.ma.getmaskarray(arr)]
        print(f"    min={float(valid.min()):.4f}, max={float(valid.max()):.4f}")
        print(f"    n_valid={valid.size}, n_total={arr.size}")
        print(f"    pct_missing={100*(1 - valid.size/arr.size):.3f}%")
        # Check if any negative values
        neg = (valid < 0).sum()
        print(f"    n_negative={neg}")

ds.close()

# Check TIME interpretation across files
print("\n" + "="*60)
print("TIME VARIABLE ACROSS ALL YEARS")
print("="*60)
for fname in nc_files:
    fpath = os.path.join(rainfall_dir, fname)
    ds = nc4.Dataset(fpath, "r")
    time_var = ds.variables['TIME']
    time_units = getattr(time_var, 'units', 'N/A')
    time_vals = time_var[:]
    time_len = len(time_vals)
    print(f"  {fname}: n_days={time_len}, units='{time_units}', first={time_vals[0]}, last={time_vals[-1]}")
    ds.close()

# ─────────────────────────────────────────────────────────────────────────────
# GeoJSON schema from raw header
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("GEOJSON SCHEMA (from raw header reading)")
print("="*60)

geojson_files = {
    "river_network": os.path.join(BASE_DIR, "data", "raw", "hydrology", "rivers", "india_river_network.geojson"),
    "canal_network": os.path.join(BASE_DIR, "data", "raw", "hydrology", "drainage", "india_canal_network.geojson"),
    "river_basins_cwc": os.path.join(BASE_DIR, "data", "raw", "hydrology", "river_basins", "extracted", "basin_cwc.GeoJSON"),
    "waterbodies_india": os.path.join(BASE_DIR, "data", "raw", "hydrology", "water_bodies", "india", "india_surface_waterbodies.geojson"),
    "reservoirs": os.path.join(BASE_DIR, "data", "raw", "hydrology", "reservoirs", "india_reservoirs_source.geojson"),
}

for key, fpath in geojson_files.items():
    if not os.path.exists(fpath):
        print(f"\n  {key}: NOT FOUND")
        continue
    fsize_mb = round(os.path.getsize(fpath) / 1e6, 2)
    print(f"\n  {key} ({fsize_mb} MB):")
    try:
        # Read first 16KB to get schema info
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            chunk = f.read(16384)
        # Try to find the first "properties" block
        props_start = chunk.find('"properties"')
        if props_start >= 0:
            props_end = chunk.find('}', props_start + len('"properties"') + 5)
            props_snippet = chunk[props_start:props_end + 1]
            print(f"    Properties snippet: {props_snippet[:800]}")
        else:
            print(f"    Header (first 800 chars): {chunk[:800]}")
    except Exception as e:
        print(f"    ERROR: {e}")

print("\nDone.")
