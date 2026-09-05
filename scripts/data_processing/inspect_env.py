"""
Phase 3 — Step 1c: Training CSV + env package check + flood summary
"""
import os, sys, json
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ── Training CSV ────────────────────────────────────────────────────────────
csv_path = os.path.join(BASE_DIR, "data", "processed", "flood_training_dataset.csv")
df = pd.read_csv(csv_path)
print("=== Training CSV ===")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"dtypes:\n{df.dtypes}")
print(f"Label/flood cols: {[c for c in df.columns if 'label' in c.lower() or 'flood' in c.lower()]}")
label_col = next((c for c in df.columns if 'label' in c.lower() or 'flood' in c.lower()), None)
if label_col:
    print(f"Value counts [{label_col}]:\n{df[label_col].value_counts()}")
print(f"Missing values:\n{df.isnull().sum()}")
print()

# ── Flood prediction summary ─────────────────────────────────────────────────
summary_path = os.path.join(BASE_DIR, "data", "processed", "flood_prediction_summary.json")
with open(summary_path) as f:
    summary = json.load(f)
print("=== Flood Prediction Summary JSON ===")
print(json.dumps(summary, indent=2))
print()

# ── Installed packages relevant to pipeline ──────────────────────────────────
print("=== Installed packages ===")
pkgs = ["numpy","pandas","rasterio","netCDF4","geopandas","fiona","shapely",
        "pyproj","scipy","sklearn","joblib","pyarrow","fastparquet","richdem",
        "dask","xarray","bottleneck","numba","psutil"]
for pkg in pkgs:
    try:
        m = __import__(pkg.replace("-","_"))
        ver = getattr(m, "__version__", "?")
        print(f"  {pkg}: OK (v{ver})")
    except ImportError:
        print(f"  {pkg}: NOT INSTALLED")

print("\nPython:", sys.version)
