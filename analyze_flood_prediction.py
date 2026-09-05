import json

import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape


print("=" * 70)
print("FLOOD PREDICTION ANALYSIS")
print("=" * 70)

PREDICTION_FILE = r"data\processed\flood_prediction.tif"
REFERENCE_FILE = r"data\processed\gfm_flood_reference.tif"

OUTPUT_JSON = r"data\processed\flood_prediction_summary.json"


# ---------------------------------------------------------------------
# Open prediction raster
# ---------------------------------------------------------------------

print()
print("Opening prediction raster...")

with rasterio.open(PREDICTION_FILE) as src:

    prediction = src.read(1)

    transform = src.transform
    crs = src.crs

    width = src.width
    height = src.height

    bounds = src.bounds

    pixel_width = abs(src.transform.a)
    pixel_height = abs(src.transform.e)

    print("Size:", width, "x", height)
    print("CRS:", crs)
    print("Bounds:", bounds)
    print("Resolution:", src.res)


# ---------------------------------------------------------------------
# Validate prediction values
# ---------------------------------------------------------------------

print()
print("Validating prediction values...")

valid_mask = np.isin(prediction, [0, 1])

invalid_pixels = int((~valid_mask).sum())

print("Invalid pixels:", invalid_pixels)

if invalid_pixels > 0:
    raise ValueError(
        f"Prediction raster contains {invalid_pixels} invalid pixels."
    )


# ---------------------------------------------------------------------
# Pixel statistics
# ---------------------------------------------------------------------

total_pixels = int(prediction.size)

flood_pixels = int((prediction == 1).sum())

non_flood_pixels = int((prediction == 0).sum())

flood_percentage = (
    flood_pixels / total_pixels * 100
)


print()
print("=" * 70)
print("PREDICTION STATISTICS")
print("=" * 70)

print("Total pixels:", total_pixels)
print("Flood pixels:", flood_pixels)
print("Non-flood pixels:", non_flood_pixels)
print("Flood percentage:", round(flood_percentage, 4), "%")


# ---------------------------------------------------------------------
# Calculate pixel area
# ---------------------------------------------------------------------

# The raster is EPSG:4326, therefore pixel dimensions are in degrees.
#
# For the small study area we use a geodesic calculation through
# rasterio's transform and latitude-dependent approximation.

mean_latitude = (
    (bounds.top + bounds.bottom) / 2.0
)

meters_per_degree_lat = 111320.0

meters_per_degree_lon = (
    111320.0 * np.cos(np.radians(mean_latitude))
)

pixel_width_m = pixel_width * meters_per_degree_lon
pixel_height_m = pixel_height * meters_per_degree_lat

pixel_area_m2 = pixel_width_m * pixel_height_m

flood_area_m2 = flood_pixels * pixel_area_m2
flood_area_km2 = flood_area_m2 / 1_000_000

total_area_m2 = total_pixels * pixel_area_m2
total_area_km2 = total_area_m2 / 1_000_000


print()
print("=" * 70)
print("AREA ESTIMATION")
print("=" * 70)

print("Approximate pixel area:", round(pixel_area_m2, 2), "m²")
print("Total study area:", round(total_area_km2, 4), "km²")
print("Estimated flooded area:", round(flood_area_km2, 4), "km²")


# ---------------------------------------------------------------------
# Determine risk level
# ---------------------------------------------------------------------

if flood_percentage < 1:
    risk_level = "LOW"

elif flood_percentage < 3:
    risk_level = "MODERATE"

elif flood_percentage < 10:
    risk_level = "HIGH"

else:
    risk_level = "VERY_HIGH"


print()
print("=" * 70)
print("RISK SUMMARY")
print("=" * 70)

print("Risk level:", risk_level)


# ---------------------------------------------------------------------
# Compare with GFM reference
# ---------------------------------------------------------------------

print()
print("=" * 70)
print("GFM REFERENCE COMPARISON")
print("=" * 70)

with rasterio.open(REFERENCE_FILE) as src:

    reference = src.read(1)

    reference_valid = reference != 255

    reference_flood = (
        (reference == 1) &
        reference_valid
    )

    reference_non_flood = (
        (reference == 0) &
        reference_valid
    )


# Make sure the grids match.

if reference.shape != prediction.shape:
    raise ValueError(
        "Prediction and GFM reference dimensions do not match."
    )


comparison_mask = (
    reference_valid &
    valid_mask
)


pred_flood = prediction == 1

ref_flood = reference == 1


true_positive = int(
    (pred_flood & ref_flood & comparison_mask).sum()
)

false_positive = int(
    (pred_flood & ~ref_flood & comparison_mask).sum()
)

false_negative = int(
    (~pred_flood & ref_flood & comparison_mask).sum()
)

true_negative = int(
    (~pred_flood & ~ref_flood & comparison_mask).sum()
)


intersection = true_positive

union = (
    true_positive +
    false_positive +
    false_negative
)


if union > 0:
    iou = intersection / union
else:
    iou = 0.0


dice_denominator = (
    2 * true_positive +
    false_positive +
    false_negative
)


if dice_denominator > 0:
    dice = (
        2 * true_positive /
        dice_denominator
    )
else:
    dice = 0.0


print("True Positive :", true_positive)
print("False Positive:", false_positive)
print("False Negative:", false_negative)
print("True Negative :", true_negative)

print()
print("IoU :", round(iou, 6))
print("Dice:", round(dice, 6))


# ---------------------------------------------------------------------
# Create citizen-facing summary
# ---------------------------------------------------------------------

summary = {
    "dataset": {
        "prediction_file": PREDICTION_FILE,
        "reference_file": REFERENCE_FILE,
        "width": width,
        "height": height,
        "crs": str(crs),
    },

    "prediction": {
        "total_pixels": total_pixels,
        "flood_pixels": flood_pixels,
        "non_flood_pixels": non_flood_pixels,
        "flood_percentage": round(flood_percentage, 6),
    },

    "area": {
        "total_area_km2": round(total_area_km2, 6),
        "flooded_area_km2": round(flood_area_km2, 6),
        "pixel_area_m2": round(pixel_area_m2, 6),
    },

    "risk": {
        "level": risk_level,
    },

    "validation": {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "iou": round(iou, 6),
        "dice": round(dice, 6),
    },
}


# ---------------------------------------------------------------------
# Save JSON
# ---------------------------------------------------------------------

print()
print("Saving flood intelligence summary...")

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=2
    )


print()
print("=" * 70)
print("FLOOD PREDICTION ANALYSIS COMPLETE")
print("=" * 70)

print()
print("Saved:", OUTPUT_JSON)