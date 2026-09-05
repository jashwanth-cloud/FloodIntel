import os
import rasterio
import numpy as np
import pandas as pd

FEATURE_FILE = r"data\processed\satellite_features_normalized.tif"
REFERENCE_FILE = r"data\processed\gfm_flood_reference.tif"

OUTPUT_FILE = r"data\processed\flood_training_dataset.csv"


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
print("FLOOD ML TRAINING DATASET GENERATION")
print("=" * 70)

print()
print("Feature file:")
print(FEATURE_FILE)

print()
print("Reference file:")
print(REFERENCE_FILE)


# ------------------------------------------------------------------
# OPEN FEATURE RASTER
# ------------------------------------------------------------------

print()
print("Opening feature raster...")

with rasterio.open(FEATURE_FILE) as src:
    features = src.read()
    feature_crs = src.crs
    feature_width = src.width
    feature_height = src.height
    feature_transform = src.transform
    feature_bounds = src.bounds

print("Feature shape:", features.shape)
print("Feature CRS:", feature_crs)
print("Feature size:", feature_width, "x", feature_height)
print("Feature transform:", feature_transform)


# ------------------------------------------------------------------
# OPEN GFM REFERENCE
# ------------------------------------------------------------------

print()
print("Opening GFM reference raster...")

with rasterio.open(REFERENCE_FILE) as src:
    reference = src.read(1)
    reference_crs = src.crs
    reference_width = src.width
    reference_height = src.height
    reference_transform = src.transform
    reference_bounds = src.bounds
    reference_nodata = src.nodata

print("Reference shape:", reference.shape)
print("Reference CRS:", reference_crs)
print("Reference size:", reference_width, "x", reference_height)
print("Reference nodata:", reference_nodata)
print("Reference transform:", reference_transform)


# ------------------------------------------------------------------
# GRID VALIDATION
# ------------------------------------------------------------------

print()
print("Validating raster alignment...")

if feature_width != reference_width:
    raise ValueError(
        f"Raster widths do not match: "
        f"{feature_width} != {reference_width}"
    )

if feature_height != reference_height:
    raise ValueError(
        f"Raster heights do not match: "
        f"{feature_height} != {reference_height}"
    )

if feature_crs != reference_crs:
    raise ValueError(
        f"Raster CRS does not match: "
        f"{feature_crs} != {reference_crs}"
    )

# Raster transforms contain floating-point values.
# Tiny differences are acceptable when the rasters were generated
# from the same intended grid.

transform_matches = np.allclose(
    np.array(feature_transform),
    np.array(reference_transform),
    rtol=0.0,
    atol=1e-9,
)

if not transform_matches:

    print()
    print("WARNING: Raster transforms differ slightly.")
    print("This can happen because of floating-point precision")
    print("during reprojection.")

    print()
    print("Feature bounds:")
    print(feature_bounds)

    print()
    print("Reference bounds:")
    print(reference_bounds)

    # Compare bounds using a small tolerance.
    bounds_matches = np.allclose(
        np.array(feature_bounds),
        np.array(reference_bounds),
        rtol=0.0,
        atol=1e-7,
    )

    if not bounds_matches:
        raise ValueError(
            "Feature and reference spatial grids do not match."
        )

    print()
    print("Bounds match within tolerance.")
    print("Continuing with pixel-to-pixel alignment.")

else:
    print("Transform alignment: OK")


# ------------------------------------------------------------------
# FEATURE COUNT VALIDATION
# ------------------------------------------------------------------

if features.shape[0] != len(FEATURE_NAMES):
    raise ValueError(
        f"Expected {len(FEATURE_NAMES)} features, "
        f"but raster contains {features.shape[0]} bands."
    )

print("Feature count: OK")


# ------------------------------------------------------------------
# RESHAPE FEATURES
# ------------------------------------------------------------------

print()
print("Preparing pixel feature matrix...")

# Original:
#
# (11, 512, 512)
#
# Converted to:
#
# (262144, 11)

X = features.reshape(
    features.shape[0],
    -1,
).T


# Reference:
#
# (512, 512)
#
# Converted to:
#
# (262144,)

y = reference.reshape(-1)


print("Feature matrix shape:", X.shape)
print("Label vector shape:", y.shape)


# ------------------------------------------------------------------
# VALID PIXEL MASK
# ------------------------------------------------------------------

print()
print("Filtering invalid pixels...")

valid_mask = np.ones(
    y.shape,
    dtype=bool,
)


# Remove reference nodata.
if reference_nodata is not None:
    valid_mask &= y != reference_nodata


# Remove NaN / infinite feature values.
valid_mask &= np.all(
    np.isfinite(X),
    axis=1,
)


# Normalized features must remain within 0-1.
valid_mask &= np.all(
    (X >= 0.0) & (X <= 1.0),
    axis=1,
)


X_valid = X[valid_mask]
y_valid = y[valid_mask]


print("Total pixels:", len(y))
print("Valid pixels:", len(y_valid))
print("Removed pixels:", len(y) - len(y_valid))


# ------------------------------------------------------------------
# LABEL VALIDATION
# ------------------------------------------------------------------

print()
print("Validating GFM labels...")

unique_labels, label_counts = np.unique(
    y_valid,
    return_counts=True,
)


for label, count in zip(
    unique_labels,
    label_counts,
):

    print(
        "Label:",
        int(label),
        "Pixels:",
        int(count),
        "Percent:",
        round(
            float(count) / len(y_valid) * 100,
            4,
        ),
    )


allowed_labels = {0, 1}

unexpected_labels = (
    set(unique_labels.astype(int))
    - allowed_labels
)

if unexpected_labels:

    raise ValueError(
        f"Unexpected GFM labels found: "
        f"{unexpected_labels}"
    )


# ------------------------------------------------------------------
# CREATE DATAFRAME
# ------------------------------------------------------------------

print()
print("Creating training dataframe...")

df = pd.DataFrame(
    X_valid,
    columns=FEATURE_NAMES,
)

df["flood_label"] = y_valid.astype(
    np.uint8
)


# ------------------------------------------------------------------
# SAVE DATASET
# ------------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True,
)


print()
print("Saving dataset...")

df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ------------------------------------------------------------------
# FINAL VERIFICATION
# ------------------------------------------------------------------

print()
print("=" * 70)
print("TRAINING DATASET VERIFICATION")
print("=" * 70)

print()
print("Output file:", OUTPUT_FILE)
print("Rows:", len(df))
print("Columns:", len(df.columns))


print()
print("Features:")

for name in FEATURE_NAMES:
    print(" -", name)


print()
print("Label column:")
print(" - flood_label")


print()
print("Class distribution:")

class_counts = (
    df["flood_label"]
    .value_counts()
    .sort_index()
)


for label, count in class_counts.items():

    print(
        "Class:",
        int(label),
        "Pixels:",
        int(count),
        "Percent:",
        round(
            float(count) / len(df) * 100,
            4,
        ),
    )


print()
print("First 5 rows:")

print(
    df.head()
)


print()
print("=" * 70)
print("TRAINING DATASET GENERATION COMPLETE")
print("=" * 70)

print()
print("Saved:", OUTPUT_FILE)