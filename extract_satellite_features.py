import numpy as np
import rasterio
from pathlib import Path

# ============================================================
# SENTINEL-1 FLOOD-CHANGE FEATURE EXTRACTION
# ============================================================

AOI_DIR = Path("flood_aoi")
OUTPUT_DIR = Path("data/processed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BEFORE_FILE = AOI_DIR / "before_vv_vh.tiff"
AFTER_FILE = AOI_DIR / "after_vv_vh.tiff"

OUTPUT_FILE = OUTPUT_DIR / "satellite_features.tif"

print("=" * 70)
print("SENTINEL-1 FLOOD-CHANGE FEATURE EXTRACTION")
print("=" * 70)

# ------------------------------------------------------------
# Check input files
# ------------------------------------------------------------

if not BEFORE_FILE.exists():
    raise FileNotFoundError(f"Before raster not found: {BEFORE_FILE}")

if not AFTER_FILE.exists():
    raise FileNotFoundError(f"After raster not found: {AFTER_FILE}")

print()
print("Before file:", BEFORE_FILE)
print("After file :", AFTER_FILE)

# ------------------------------------------------------------
# Read BEFORE raster
# ------------------------------------------------------------

with rasterio.open(BEFORE_FILE) as before_src:

    before = before_src.read().astype(np.float32)

    profile = before_src.profile.copy()

    print()
    print("BEFORE RASTER")
    print("Size :", before_src.width, "x", before_src.height)
    print("Bands:", before_src.count)
    print("CRS  :", before_src.crs)

# ------------------------------------------------------------
# Read AFTER raster
# ------------------------------------------------------------

with rasterio.open(AFTER_FILE) as after_src:

    after = after_src.read().astype(np.float32)

    print()
    print("AFTER RASTER")
    print("Size :", after_src.width, "x", after_src.height)
    print("Bands:", after_src.count)
    print("CRS  :", after_src.crs)

# ------------------------------------------------------------
# Validate raster dimensions
# ------------------------------------------------------------

if before.shape != after.shape:
    raise ValueError(
        f"Raster shape mismatch: BEFORE={before.shape}, AFTER={after.shape}"
    )

print()
print("Raster shape:", before.shape)

# ------------------------------------------------------------
# Validate band structure
#
# Band 1 = VV
# Band 2 = VH
# ------------------------------------------------------------

if before.shape[0] < 2 or after.shape[0] < 2:
    raise ValueError(
        "Both rasters must contain at least VV and VH bands."
    )

before_vv = before[0]
before_vh = before[1]

after_vv = after[0]
after_vh = after[1]

# ------------------------------------------------------------
# Replace invalid values
# ------------------------------------------------------------

before_vv = np.nan_to_num(
    before_vv,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

before_vh = np.nan_to_num(
    before_vh,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

after_vv = np.nan_to_num(
    after_vv,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

after_vh = np.nan_to_num(
    after_vh,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

# ------------------------------------------------------------
# Calculate satellite change features
# ------------------------------------------------------------

# Absolute backscatter change
vv_change = after_vv - before_vv
vh_change = after_vh - before_vh

# Ratio change
epsilon = 1e-6

vv_ratio = after_vv / (before_vv + epsilon)
vh_ratio = after_vh / (before_vh + epsilon)

# VV/VH relationship
before_vv_vh_ratio = before_vv / (before_vh + epsilon)
after_vv_vh_ratio = after_vv / (after_vh + epsilon)

vv_vh_change = after_vv_vh_ratio - before_vv_vh_ratio

# ------------------------------------------------------------
# Build feature stack
#
# 1  = Before VV
# 2  = Before VH
# 3  = After VV
# 4  = After VH
# 5  = VV change
# 6  = VH change
# 7  = VV ratio
# 8  = VH ratio
# 9  = Before VV/VH ratio
# 10 = After VV/VH ratio
# 11 = VV/VH ratio change
# ------------------------------------------------------------

features = np.stack(
    [
        before_vv,
        before_vh,
        after_vv,
        after_vh,
        vv_change,
        vh_change,
        vv_ratio,
        vh_ratio,
        before_vv_vh_ratio,
        after_vv_vh_ratio,
        vv_vh_change,
    ],
    axis=0,
).astype(np.float32)

# ------------------------------------------------------------
# Clean extreme numerical values
# ------------------------------------------------------------

features = np.nan_to_num(
    features,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

# ------------------------------------------------------------
# Update GeoTIFF profile
# ------------------------------------------------------------

profile.update(
    driver="GTiff",
    dtype="float32",
    count=features.shape[0],
    compress="deflate",
    predictor=2,
    tiled=True,
    blockxsize=256,
    blockysize=256,
)

# ------------------------------------------------------------
# Write feature raster
# ------------------------------------------------------------

print()
print("Writing feature raster...")

with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:

    for band_index in range(features.shape[0]):
        dst.write(
            features[band_index],
            band_index + 1,
        )

# ------------------------------------------------------------
# Feature names
# ------------------------------------------------------------

feature_names = [
    "before_vv",
    "before_vh",
    "after_vv",
    "after_vh",
    "vv_change",
    "vh_change",
    "vv_ratio",
    "vh_ratio",
    "before_vv_vh_ratio",
    "after_vv_vh_ratio",
    "vv_vh_change",
]

# ------------------------------------------------------------
# Feature statistics
# ------------------------------------------------------------

print()
print("=" * 70)
print("FEATURE STATISTICS")
print("=" * 70)

for index, name in enumerate(feature_names):

    band = features[index]

    print()
    print(name)
    print("  min :", float(np.min(band)))
    print("  max :", float(np.max(band)))
    print("  mean:", float(np.mean(band)))

# ------------------------------------------------------------
# Verify output
# ------------------------------------------------------------

with rasterio.open(OUTPUT_FILE) as check:

    print()
    print("=" * 70)
    print("OUTPUT VERIFICATION")
    print("=" * 70)

    print()
    print("Output file :", OUTPUT_FILE)
    print("Size        :", check.width, "x", check.height)
    print("Bands       :", check.count)
    print("CRS         :", check.crs)
    print("Data type   :", check.dtypes[0])
    print("Block size  :", check.block_shapes[0])

# ------------------------------------------------------------
# Complete
# ------------------------------------------------------------

print()
print("=" * 70)
print("SATELLITE FEATURE EXTRACTION COMPLETE")
print("=" * 70)

print()
print("Features:", features.shape[0])
print("Raster size:", features.shape[2], "x", features.shape[1])
print("Saved:", OUTPUT_FILE)