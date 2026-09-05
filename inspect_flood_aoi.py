import rasterio
import numpy as np
from pathlib import Path

# ============================================================
# GROWRISEMIND — FLOOD AOI RASTER INSPECTION
# ============================================================

INPUT_DIR = Path("flood_aoi")

FILES = {
    "BEFORE": INPUT_DIR / "before_vv_vh.tiff",
    "AFTER": INPUT_DIR / "after_vv_vh.tiff",
}

print("=" * 70)
print("GROWRISEMIND — FLOOD AOI RASTER INSPECTION")
print("=" * 70)


def inspect_raster(label, file_path):

    print()
    print("=" * 70)
    print(f"{label} SCENE")
    print("=" * 70)

    if not file_path.exists():
        print("ERROR: File not found:")
        print(file_path)
        return False

    print("File:", file_path)
    print(
        "File size:",
        round(file_path.stat().st_size / 1024, 2),
        "KB"
    )

    try:

        with rasterio.open(file_path) as src:

            print()
            print("RASTER INFORMATION")
            print("-" * 70)

            print("Driver       :", src.driver)
            print("Width        :", src.width)
            print("Height       :", src.height)
            print("Band count   :", src.count)
            print("CRS          :", src.crs)
            print("Data type    :", src.dtypes)
            print("Resolution   :", src.res)
            print("NoData       :", src.nodata)
            print("Bounds       :", src.bounds)

            print()
            print("BAND INFORMATION")
            print("-" * 70)

            for band_number in range(1, src.count + 1):

                data = src.read(band_number)

                valid = np.isfinite(data)

                if src.nodata is not None:
                    valid &= data != src.nodata

                valid_values = data[valid]

                print()
                print(f"Band {band_number}")

                if len(valid_values) == 0:
                    print("  No valid pixels found.")
                    continue

                print(
                    "  Valid pixels :",
                    len(valid_values)
                )

                print(
                    "  Min          :",
                    float(np.min(valid_values))
                )

                print(
                    "  Max          :",
                    float(np.max(valid_values))
                )

                print(
                    "  Mean         :",
                    float(np.mean(valid_values))
                )

                print(
                    "  Median       :",
                    float(np.median(valid_values))
                )

                print(
                    "  Std deviation:",
                    float(np.std(valid_values))
                )

                print(
                    "  P01          :",
                    float(np.percentile(valid_values, 1))
                )

                print(
                    "  P05          :",
                    float(np.percentile(valid_values, 5))
                )

                print(
                    "  P95          :",
                    float(np.percentile(valid_values, 95))
                )

                print(
                    "  P99          :",
                    float(np.percentile(valid_values, 99))
                )

                zero_pixels = np.sum(valid_values == 0)

                print(
                    "  Zero pixels  :",
                    int(zero_pixels)
                )

            print()
            print("SAMPLE PIXELS")
            print("-" * 70)

            for band_number in range(1, src.count + 1):

                data = src.read(band_number)

                center_y = src.height // 2
                center_x = src.width // 2

                y_start = max(0, center_y - 2)
                y_end = min(src.height, center_y + 3)

                x_start = max(0, center_x - 2)
                x_end = min(src.width, center_x + 3)

                sample = data[
                    y_start:y_end,
                    x_start:x_end
                ]

                print(
                    f"Band {band_number} "
                    "center 5x5:"
                )

                print(sample)

            return True

    except Exception as e:

        print()
        print("ERROR READING RASTER:")
        print(e)

        return False


# ============================================================
# INSPECT BOTH SCENES
# ============================================================

before_ok = inspect_raster(
    "BEFORE",
    FILES["BEFORE"]
)

after_ok = inspect_raster(
    "AFTER",
    FILES["AFTER"]
)


# ============================================================
# FINAL STATUS
# ============================================================

print()
print("=" * 70)
print("RASTER INSPECTION COMPLETE")
print("=" * 70)

print()

if before_ok and after_ok:

    print("BEFORE raster: VALID")
    print("AFTER raster : VALID")

    print()
    print("Both AOI rasters are ready for flood-change analysis.")

else:

    print("Raster inspection found a problem.")

    if not before_ok:
        print("  BEFORE raster requires attention.")

    if not after_ok:
        print("  AFTER raster requires attention.")