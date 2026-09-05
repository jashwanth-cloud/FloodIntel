import csv
from pathlib import Path

import numpy as np
import rasterio


# ============================================================
# SATELLITE FLOOD-CHANGE SUMMARY
# ============================================================

INPUT_FILE = Path(
    "data/processed/satellite_features.tif"
)

OUTPUT_FILE = Path(
    "data/processed/satellite_change_summary.csv"
)

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
print("SATELLITE FLOOD-CHANGE SUMMARY")
print("=" * 70)


# ------------------------------------------------------------
# Check input
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input feature raster not found: {INPUT_FILE}"
    )


# ------------------------------------------------------------
# Read raster
# ------------------------------------------------------------

with rasterio.open(INPUT_FILE) as src:

    print()
    print("Input:", INPUT_FILE)
    print("Size:", src.width, "x", src.height)
    print("Bands:", src.count)
    print("CRS:", src.crs)

    features = src.read().astype(np.float32)

    bounds = src.bounds

    width = src.width
    height = src.height
    crs = str(src.crs)

    transform = src.transform

    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)


# ------------------------------------------------------------
# Validate
# ------------------------------------------------------------

if features.shape[0] != len(FEATURE_NAMES):
    raise ValueError(
        f"Expected {len(FEATURE_NAMES)} bands, "
        f"found {features.shape[0]}"
    )


# ------------------------------------------------------------
# Helper function
# ------------------------------------------------------------

def statistics(values):
    """
    Return basic statistics for a raster feature.
    """

    values = values[np.isfinite(values)]

    if values.size == 0:
        return {
            "min": 0.0,
            "p01": 0.0,
            "p05": 0.0,
            "median": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "max": 0.0,
            "mean": 0.0,
        }

    return {
        "min": float(np.min(values)),
        "p01": float(np.percentile(values, 1)),
        "p05": float(np.percentile(values, 5)),
        "median": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
        "p99": float(np.percentile(values, 99)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
    }


# ------------------------------------------------------------
# Build feature statistics
# ------------------------------------------------------------

rows = []

print()
print("=" * 70)
print("FEATURE STATISTICS")
print("=" * 70)

for index, name in enumerate(FEATURE_NAMES):

    band = features[index]

    stats = statistics(band)

    row = {
        "feature": name,
        **stats,
    }

    rows.append(row)

    print()
    print(name)
    print("  min   :", stats["min"])
    print("  p01   :", stats["p01"])
    print("  p05   :", stats["p05"])
    print("  median:", stats["median"])
    print("  p95   :", stats["p95"])
    print("  p99   :", stats["p99"])
    print("  max   :", stats["max"])
    print("  mean  :", stats["mean"])


# ------------------------------------------------------------
# Flood-change indicators
#
# These are descriptive indicators only.
# They are NOT flood labels.
# ------------------------------------------------------------

vv_change = features[4]
vh_change = features[5]

valid_vv = vv_change[np.isfinite(vv_change)]
valid_vh = vh_change[np.isfinite(vh_change)]

# Strong positive change thresholds.
#
# Using the 95th percentile makes the indicator relative
# to this particular scene rather than imposing an arbitrary
# physical threshold.
#
# These percentages should NOT be interpreted as flooded area.
# They simply describe the strongest change pixels.

vv_threshold = np.percentile(valid_vv, 95)
vh_threshold = np.percentile(valid_vh, 95)

vv_strong_change = (
    valid_vv >= vv_threshold
)

vh_strong_change = (
    valid_vh >= vh_threshold
)

vv_strong_percentage = (
    np.count_nonzero(vv_strong_change)
    / valid_vv.size
    * 100.0
)

vh_strong_percentage = (
    np.count_nonzero(vh_strong_change)
    / valid_vh.size
    * 100.0
)


# ------------------------------------------------------------
# Geographic information
# ------------------------------------------------------------

west = float(bounds.left)
south = float(bounds.bottom)
east = float(bounds.right)
north = float(bounds.top)


# ------------------------------------------------------------
# Create summary records
# ------------------------------------------------------------

summary_rows = [
    {
        "metric": "raster_width",
        "value": width,
        "unit": "pixels",
    },
    {
        "metric": "raster_height",
        "value": height,
        "unit": "pixels",
    },
    {
        "metric": "band_count",
        "value": len(FEATURE_NAMES),
        "unit": "bands",
    },
    {
        "metric": "crs",
        "value": crs,
        "unit": "",
    },
    {
        "metric": "pixel_width",
        "value": pixel_width,
        "unit": "degrees",
    },
    {
        "metric": "pixel_height",
        "value": pixel_height,
        "unit": "degrees",
    },
    {
        "metric": "west",
        "value": west,
        "unit": "degrees",
    },
    {
        "metric": "south",
        "value": south,
        "unit": "degrees",
    },
    {
        "metric": "east",
        "value": east,
        "unit": "degrees",
    },
    {
        "metric": "north",
        "value": north,
        "unit": "degrees",
    },
    {
        "metric": "vv_change_95th_percentile",
        "value": float(vv_threshold),
        "unit": "backscatter units",
    },
    {
        "metric": "vh_change_95th_percentile",
        "value": float(vh_threshold),
        "unit": "backscatter units",
    },
    {
        "metric": "vv_top_5_percent_change_pixels",
        "value": float(vv_strong_percentage),
        "unit": "percent",
    },
    {
        "metric": "vh_top_5_percent_change_pixels",
        "value": float(vh_strong_percentage),
        "unit": "percent",
    },
]


# ------------------------------------------------------------
# Add feature statistics to summary
# ------------------------------------------------------------

for row in rows:

    feature = row["feature"]

    summary_rows.extend(
        [
            {
                "metric": f"{feature}_min",
                "value": row["min"],
                "unit": "feature units",
            },
            {
                "metric": f"{feature}_median",
                "value": row["median"],
                "unit": "feature units",
            },
            {
                "metric": f"{feature}_mean",
                "value": row["mean"],
                "unit": "feature units",
            },
            {
                "metric": f"{feature}_p95",
                "value": row["p95"],
                "unit": "feature units",
            },
            {
                "metric": f"{feature}_p99",
                "value": row["p99"],
                "unit": "feature units",
            },
            {
                "metric": f"{feature}_max",
                "value": row["max"],
                "unit": "feature units",
            },
        ]
    )


# ------------------------------------------------------------
# Write CSV
# ------------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8",
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "metric",
            "value",
            "unit",
        ],
    )

    writer.writeheader()
    writer.writerows(summary_rows)


# ------------------------------------------------------------
# Print important summary
# ------------------------------------------------------------

print()
print("=" * 70)
print("SATELLITE CHANGE SUMMARY")
print("=" * 70)

print()
print("VV change mean:", float(np.mean(valid_vv)))
print("VH change mean:", float(np.mean(valid_vh)))

print()
print("VV change 95th percentile:", float(vv_threshold))
print("VH change 95th percentile:", float(vh_threshold))

print()
print(
    "Pixels in strongest 5% of VV change:",
    f"{vv_strong_percentage:.2f}%"
)

print(
    "Pixels in strongest 5% of VH change:",
    f"{vh_strong_percentage:.2f}%"
)

print()
print("IMPORTANT:")
print(
    "These percentages describe strong SAR change only."
)
print(
    "They are NOT interpreted as flooded-area percentages."
)


# ------------------------------------------------------------
# Complete
# ------------------------------------------------------------

print()
print("=" * 70)
print("SUMMARY GENERATION COMPLETE")
print("=" * 70)

print()
print("Saved:", OUTPUT_FILE)