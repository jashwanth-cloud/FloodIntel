import numpy as np
import rasterio
from pathlib import Path

# ============================================================
# SATELLITE FEATURE QUALITY CONTROL + NORMALIZATION
# ============================================================

INPUT_FILE = Path("data/processed/satellite_features.tif")
OUTPUT_DIR = Path("data/processed")

OUTPUT_FILE = OUTPUT_DIR / "satellite_features_normalized.tif"
REPORT_FILE = OUTPUT_DIR / "satellite_feature_quality_report.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Feature definitions
# ------------------------------------------------------------

FEATURE_NAMES = [
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

print("=" * 70)
print("SATELLITE FEATURE QUALITY CONTROL")
print("=" * 70)

# ------------------------------------------------------------
# Check input
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Feature raster not found: {INPUT_FILE}"
    )

# ------------------------------------------------------------
# Read feature raster
# ------------------------------------------------------------

with rasterio.open(INPUT_FILE) as src:

    features = src.read().astype(np.float32)
    profile = src.profile.copy()

    print()
    print("Input:", INPUT_FILE)
    print("Size:", src.width, "x", src.height)
    print("Bands:", src.count)
    print("CRS:", src.crs)

# ------------------------------------------------------------
# Validate feature count
# ------------------------------------------------------------

if features.shape[0] != len(FEATURE_NAMES):
    raise ValueError(
        f"Expected {len(FEATURE_NAMES)} features, "
        f"but found {features.shape[0]}"
    )

# ------------------------------------------------------------
# Quality analysis
# ------------------------------------------------------------

report_rows = []

print()
print("=" * 70)
print("FEATURE QUALITY REPORT")
print("=" * 70)

for index, name in enumerate(FEATURE_NAMES):

    band = features[index]

    finite_mask = np.isfinite(band)

    finite_values = band[finite_mask]

    if finite_values.size == 0:
        raise ValueError(
            f"No valid values found for feature: {name}"
        )

    p01 = np.percentile(finite_values, 1)
    p05 = np.percentile(finite_values, 5)
    p25 = np.percentile(finite_values, 25)
    p50 = np.percentile(finite_values, 50)
    p75 = np.percentile(finite_values, 75)
    p95 = np.percentile(finite_values, 95)
    p99 = np.percentile(finite_values, 99)

    minimum = np.min(finite_values)
    maximum = np.max(finite_values)
    mean = np.mean(finite_values)

    invalid_count = np.count_nonzero(~finite_mask)

    report_rows.append(
        {
            "feature": name,
            "min": float(minimum),
            "p01": float(p01),
            "p05": float(p05),
            "p25": float(p25),
            "median": float(p50),
            "p75": float(p75),
            "p95": float(p95),
            "p99": float(p99),
            "max": float(maximum),
            "mean": float(mean),
            "invalid_pixels": int(invalid_count),
        }
    )

    print()
    print(name)
    print("  min :", float(minimum))
    print("  p01 :", float(p01))
    print("  p05 :", float(p05))
    print("  p25 :", float(p25))
    print("  median:", float(p50))
    print("  p75 :", float(p75))
    print("  p95 :", float(p95))
    print("  p99 :", float(p99))
    print("  max :", float(maximum))
    print("  mean:", float(mean))
    print("  invalid pixels:", int(invalid_count))

# ------------------------------------------------------------
# Save quality report
# ------------------------------------------------------------

import csv

with open(
    REPORT_FILE,
    "w",
    newline="",
    encoding="utf-8",
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "feature",
            "min",
            "p01",
            "p05",
            "p25",
            "median",
            "p75",
            "p95",
            "p99",
            "max",
            "mean",
            "invalid_pixels",
        ],
    )

    writer.writeheader()
    writer.writerows(report_rows)

print()
print("Quality report saved:")
print(REPORT_FILE)

# ------------------------------------------------------------
# Normalize features
#
# We use percentile clipping:
#
# lower = 1st percentile
# upper = 99th percentile
#
# Values outside that range are clipped.
#
# Then scale to approximately 0..1.
# ------------------------------------------------------------

normalized = np.zeros_like(features, dtype=np.float32)

print()
print("=" * 70)
print("NORMALIZING FEATURES")
print("=" * 70)

for index, name in enumerate(FEATURE_NAMES):

    band = features[index]

    finite_mask = np.isfinite(band)

    valid_values = band[finite_mask]

    lower = np.percentile(valid_values, 1)
    upper = np.percentile(valid_values, 99)

    # Avoid division by zero
    if upper <= lower:
        normalized[index] = 0.0
        continue

    clipped = np.clip(
        band,
        lower,
        upper,
    )

    scaled = (
        (clipped - lower)
        / (upper - lower)
    )

    # Invalid values become zero
    scaled[~finite_mask] = 0.0

    normalized[index] = scaled.astype(np.float32)

    print()
    print(name)
    print("  clipping lower:", float(lower))
    print("  clipping upper:", float(upper))
    print("  normalized min :", float(np.min(normalized[index])))
    print("  normalized max :", float(np.max(normalized[index])))
    print("  normalized mean:", float(np.mean(normalized[index])))

# ------------------------------------------------------------
# Update output profile
# ------------------------------------------------------------

profile.update(
    driver="GTiff",
    dtype="float32",
    count=len(FEATURE_NAMES),
    compress="deflate",
    predictor=2,
    tiled=True,
    blockxsize=256,
    blockysize=256,
)

# ------------------------------------------------------------
# Write normalized raster
# ------------------------------------------------------------

print()
print("Writing normalized feature raster...")

with rasterio.open(
    OUTPUT_FILE,
    "w",
    **profile,
) as dst:

    for index in range(len(FEATURE_NAMES)):

        dst.write(
            normalized[index],
            index + 1,
        )

# ------------------------------------------------------------
# Verify output
# ------------------------------------------------------------

with rasterio.open(OUTPUT_FILE) as check:

    print()
    print("=" * 70)
    print("OUTPUT VERIFICATION")
    print("=" * 70)

    print()
    print("Output file:", OUTPUT_FILE)
    print("Size:", check.width, "x", check.height)
    print("Bands:", check.count)
    print("CRS:", check.crs)
    print("Data type:", check.dtypes[0])
    print("Block size:", check.block_shapes[0])

# ------------------------------------------------------------
# Complete
# ------------------------------------------------------------

print()
print("=" * 70)
print("SATELLITE NORMALIZATION COMPLETE")
print("=" * 70)

print()
print("Raw features preserved:")
print(INPUT_FILE)

print()
print("Normalized features:")
print(OUTPUT_FILE)

print()
print("Quality report:")
print(REPORT_FILE)