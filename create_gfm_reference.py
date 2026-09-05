import rasterio
import numpy as np

from pathlib import Path
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds


# ============================================================
# GFM FLOOD REFERENCE GENERATOR
# ============================================================

GFM_URL = (
    "https://data.eodc.eu/collections/GFM_LAYERS/flood_extent/"
    "AS020M/2024/09/01/"
    "ENSEMBLE_FLOOD_20240901T003107_VV_AS020M_E027N015T3.tif"
)

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "gfm_flood_reference.tif"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# TARGET GRID
# ------------------------------------------------------------

TARGET_WIDTH = 512
TARGET_HEIGHT = 512

TARGET_LEFT = 80.3865
TARGET_BOTTOM = 16.2567
TARGET_RIGHT = 80.4865
TARGET_TOP = 16.3567

TARGET_CRS = "EPSG:4326"

TARGET_TRANSFORM = from_bounds(
    TARGET_LEFT,
    TARGET_BOTTOM,
    TARGET_RIGHT,
    TARGET_TOP,
    TARGET_WIDTH,
    TARGET_HEIGHT,
)


print("=" * 70)
print("GFM FLOOD REFERENCE GENERATOR")
print("=" * 70)

print()
print("Source:")
print(GFM_URL)

print()
print("Target grid:")
print("CRS:", TARGET_CRS)
print("Size:", TARGET_WIDTH, "x", TARGET_HEIGHT)
print(
    "Bounds:",
    TARGET_LEFT,
    TARGET_BOTTOM,
    TARGET_RIGHT,
    TARGET_TOP,
)

# ------------------------------------------------------------
# OPEN SOURCE GFM RASTER
# ------------------------------------------------------------

print()
print("Opening GFM raster...")

with rasterio.open("/vsicurl/" + GFM_URL) as src:

    print("Source CRS:", src.crs)
    print("Source size:", src.width, "x", src.height)
    print("Source resolution:", src.res)
    print("Source nodata:", src.nodata)

    # --------------------------------------------------------
    # READ SOURCE
    # --------------------------------------------------------

    source = src.read(1)

    print()
    print("Source values:")

    values, counts = np.unique(source, return_counts=True)

    for value, count in zip(values, counts):

        percentage = (count / source.size) * 100

        print(
            "Value:",
            int(value),
            "Pixels:",
            int(count),
            "Percent:",
            round(percentage, 4),
        )

    # --------------------------------------------------------
    # TARGET ARRAY
    # --------------------------------------------------------

    target = np.full(
        (TARGET_HEIGHT, TARGET_WIDTH),
        255,
        dtype=np.uint8,
    )

    # --------------------------------------------------------
    # REPROJECT / RESAMPLE
    # --------------------------------------------------------

    print()
    print("Reprojecting to target grid...")

    reproject(
        source=source,
        destination=target,
        src_transform=src.transform,
        src_crs=src.crs,
        src_nodata=255,
        dst_transform=TARGET_TRANSFORM,
        dst_crs=TARGET_CRS,
        dst_nodata=255,
        resampling=Resampling.nearest,
    )


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

profile = {
    "driver": "GTiff",
    "height": TARGET_HEIGHT,
    "width": TARGET_WIDTH,
    "count": 1,
    "dtype": "uint8",
    "crs": TARGET_CRS,
    "transform": TARGET_TRANSFORM,
    "nodata": 255,
    "compress": "deflate",
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
}


print()
print("Writing reference raster...")

with rasterio.open(
    OUTPUT_FILE,
    "w",
    **profile,
) as dst:

    dst.write(target, 1)


# ------------------------------------------------------------
# VERIFY
# ------------------------------------------------------------

print()
print("=" * 70)
print("OUTPUT VERIFICATION")
print("=" * 70)

with rasterio.open(OUTPUT_FILE) as check:

    data = check.read(1)

    print("Output file:", OUTPUT_FILE)
    print("Size:", check.width, "x", check.height)
    print("Bands:", check.count)
    print("CRS:", check.crs)
    print("Data type:", check.dtypes[0])
    print("Nodata:", check.nodata)
    print("Resolution:", check.res)
    print("Bounds:", check.bounds)

    values, counts = np.unique(data, return_counts=True)

    print()
    print("Output values:")

    for value, count in zip(values, counts):

        percentage = (count / data.size) * 100

        print(
            "Value:",
            int(value),
            "Pixels:",
            int(count),
            "Percent:",
            round(percentage, 4),
        )


print()
print("=" * 70)
print("GFM REFERENCE GENERATION COMPLETE")
print("=" * 70)

print()
print("Saved:", OUTPUT_FILE)