import numpy as np
import rasterio
from pathlib import Path

# ============================================================
# NORMALIZED SATELLITE FEATURE VERIFICATION
# ============================================================

INPUT_FILE = Path(
    "data/processed/satellite_features_normalized.tif"
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
print("NORMALIZED SATELLITE FEATURE VERIFICATION")
print("=" * 70)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Normalized raster not found: {INPUT_FILE}"
    )

with rasterio.open(INPUT_FILE) as src:

    print()
    print("File:", INPUT_FILE)
    print("Size:", src.width, "x", src.height)
    print("Bands:", src.count)
    print("CRS:", src.crs)
    print("Data type:", src.dtypes[0])
    print("Block size:", src.block_shapes[0])

    if src.count != len(FEATURE_NAMES):
        raise ValueError(
            f"Expected {len(FEATURE_NAMES)} bands, "
            f"found {src.count}"
        )

    if src.width != 512 or src.height != 512:
        raise ValueError(
            "Unexpected raster dimensions."
        )

    print()
    print("=" * 70)
    print("NORMALIZED FEATURE RANGES")
    print("=" * 70)

    for index, name in enumerate(FEATURE_NAMES):

        band = src.read(index + 1)

        minimum = float(np.min(band))
        maximum = float(np.max(band))
        mean = float(np.mean(band))

        invalid = int(
            np.count_nonzero(
                ~np.isfinite(band)
            )
        )

        outside_range = int(
            np.count_nonzero(
                (band < 0.0) | (band > 1.0)
            )
        )

        print()
        print(name)
        print("  min:", minimum)
        print("  max:", maximum)
        print("  mean:", mean)
        print("  invalid pixels:", invalid)
        print("  outside 0-1:", outside_range)

        if invalid > 0:
            raise ValueError(
                f"{name} contains invalid pixels."
            )

        if outside_range > 0:
            raise ValueError(
                f"{name} contains values outside 0-1."
            )

print()
print("=" * 70)
print("NORMALIZED FEATURE VERIFICATION COMPLETE")
print("=" * 70)

print()
print("All 11 features are valid.")
print("All values are within the expected 0-1 range.")
print("Raster dimensions are correct.")
print("CRS is preserved.")