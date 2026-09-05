import joblib
import numpy as np
import rasterio


print("=" * 70)
print("FULL FLOOD PREDICTION RASTER GENERATION")
print("=" * 70)

FEATURE_FILE = r"data\processed\satellite_features_normalized.tif"
MODEL_FILE = r"data\processed\flood_random_forest_model.joblib"
OUTPUT_FILE = r"data\processed\flood_prediction.tif"


# ---------------------------------------------------------------------
# Load model
# ---------------------------------------------------------------------

print()
print("Loading trained model...")
model = joblib.load(MODEL_FILE)

print("Model loaded successfully.")


# ---------------------------------------------------------------------
# Open feature raster
# ---------------------------------------------------------------------

print()
print("Opening normalized satellite features...")

with rasterio.open(FEATURE_FILE) as src:

    features = src.read()

    profile = src.profile.copy()
    transform = src.transform
    crs = src.crs
    width = src.width
    height = src.height
    feature_count = src.count

    print("Feature shape:", features.shape)
    print("Feature count:", feature_count)
    print("Raster size:", width, "x", height)
    print("CRS:", crs)


# ---------------------------------------------------------------------
# Validate feature count
# ---------------------------------------------------------------------

expected_features = 11

if feature_count != expected_features:
    raise ValueError(
        f"Expected {expected_features} features, "
        f"but found {feature_count}."
    )

print("Feature count validation: OK")


# ---------------------------------------------------------------------
# Prepare pixel matrix
# ---------------------------------------------------------------------

print()
print("Preparing pixel feature matrix...")

# Original:
# (11, 512, 512)

# Transpose to:
# (512, 512, 11)

features_hwc = np.transpose(features, (1, 2, 0))

# Flatten pixels:
# (262144, 11)

X = features_hwc.reshape(-1, feature_count)

print("Prediction matrix shape:", X.shape)


# ---------------------------------------------------------------------
# Validate values
# ---------------------------------------------------------------------

print()
print("Checking feature values...")

invalid = np.isnan(X).any(axis=1) | np.isinf(X).any(axis=1)

invalid_count = int(invalid.sum())

print("Invalid pixels:", invalid_count)

if invalid_count > 0:
    raise ValueError(
        f"Found {invalid_count} pixels containing NaN or infinite values."
    )

print("Feature validation: OK")


# ---------------------------------------------------------------------
# Generate flood predictions
# ---------------------------------------------------------------------

print()
print("Generating flood predictions...")
print("Total pixels:", len(X))

predictions = model.predict(X)

predictions = predictions.astype(np.uint8)

print("Prediction complete.")


# ---------------------------------------------------------------------
# Verify predictions
# ---------------------------------------------------------------------

print()
print("=" * 70)
print("PREDICTION VERIFICATION")
print("=" * 70)

values, counts = np.unique(predictions, return_counts=True)

for value, count in zip(values, counts):

    percentage = (count / predictions.size) * 100

    label = "FLOOD" if value == 1 else "NON-FLOOD"

    print(
        f"{label:10s} "
        f"Value: {int(value)} "
        f"Pixels: {int(count)} "
        f"Percent: {percentage:.4f}"
    )


# ---------------------------------------------------------------------
# Reshape back to raster
# ---------------------------------------------------------------------

prediction_raster = predictions.reshape(height, width)


# ---------------------------------------------------------------------
# Configure output raster
# ---------------------------------------------------------------------

profile.update(
    dtype=rasterio.uint8,
    count=1,
    compress="lzw",
    nodata=255
)


# ---------------------------------------------------------------------
# Save prediction raster
# ---------------------------------------------------------------------

print()
print("Saving prediction raster...")

with rasterio.open(OUTPUT_FILE, "w", **profile) as dst:

    dst.write(prediction_raster, 1)

    dst.set_band_description(
        1,
        "Flood prediction: 0=non-flood, 1=flood"
    )


# ---------------------------------------------------------------------
# Final verification
# ---------------------------------------------------------------------

print()
print("=" * 70)
print("OUTPUT VERIFICATION")
print("=" * 70)

with rasterio.open(OUTPUT_FILE) as src:

    print("Output file:", OUTPUT_FILE)
    print("Size:", src.width, "x", src.height)
    print("Bands:", src.count)
    print("CRS:", src.crs)
    print("Data type:", src.dtypes[0])
    print("Nodata:", src.nodata)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)

    output = src.read(1)

    values, counts = np.unique(output, return_counts=True)

    print()
    print("Output values:")

    for value, count in zip(values, counts):

        percentage = (count / output.size) * 100

        label = "FLOOD" if value == 1 else "NON-FLOOD"

        print(
            f"{label:10s} "
            f"Value: {int(value)} "
            f"Pixels: {int(count)} "
            f"Percent: {percentage:.4f}"
        )


print()
print("=" * 70)
print("FLOOD PREDICTION RASTER GENERATION COMPLETE")
print("=" * 70)

print()
print("Saved:", OUTPUT_FILE)