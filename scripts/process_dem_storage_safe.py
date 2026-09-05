from pathlib import Path
import zipfile
import tempfile
import shutil

import rasterio
import numpy as np


# ======================================================================
# SIH 26071 — STORAGE-SAFE DEM PROCESSOR
#
# Workflow:
#   1. Find DEM ZIP in data/raw/dem
#   2. Extract it temporarily
#   3. Locate the actual DEM raster
#   4. Read and validate elevation data
#   5. Convert to Float32
#   6. Write compressed GeoTIFF
#   7. Delete temporary extraction automatically
#   8. Delete original ZIP ONLY after successful processing
#
# IMPORTANT:
# The downloaded DEM is currently only a TEST product.
# It should not be used as India's final DEM dataset.
# ======================================================================


# ----------------------------------------------------------------------
# PROJECT PATHS
# ----------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "dem"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "dem"

OUTPUT_FILE = PROCESSED_DIR / "dem_test_processed.tif"


# ----------------------------------------------------------------------
# DISPLAY
# ----------------------------------------------------------------------

def print_header():
    print("=" * 72)
    print("SIH 26071 — STORAGE-SAFE DEM PROCESSOR")
    print("=" * 72)
    print()

    print("Project:")
    print(PROJECT_ROOT)
    print()

    print("Input:")
    print(RAW_DIR)
    print()

    print("Output:")
    print(PROCESSED_DIR)
    print()


# ----------------------------------------------------------------------
# FIND DEM ZIP
# ----------------------------------------------------------------------

def find_dem_zip():
    """
    Find DEM ZIP files in the raw DEM directory.

    If multiple ZIP files exist, the largest one is selected.
    """

    zip_files = list(RAW_DIR.glob("*.zip"))

    if not zip_files:
        return None

    zip_files.sort(
        key=lambda file: file.stat().st_size,
        reverse=True
    )

    return zip_files[0]


# ----------------------------------------------------------------------
# FIND RASTER
# ----------------------------------------------------------------------

def find_dem_raster(directory):
    """
    Search recursively for a DEM raster inside the extracted product.
    """

    supported_extensions = {
        ".tif",
        ".tiff",
        ".dem",
        ".img"
    }

    raster_files = []

    for file in directory.rglob("*"):

        if not file.is_file():
            continue

        if file.suffix.lower() in supported_extensions:
            raster_files.append(file)

    if not raster_files:
        return None

    # Prefer GeoTIFF files.
    tif_files = [
        file
        for file in raster_files
        if file.suffix.lower() in {".tif", ".tiff"}
    ]

    if tif_files:
        return tif_files[0]

    return raster_files[0]


# ----------------------------------------------------------------------
# PROCESS DEM
# ----------------------------------------------------------------------

def process_dem(input_raster):
    """
    Read DEM and create a compressed Float32 GeoTIFF.

    Storage-safe:
    - only one band is processed
    - Float32 is used
    - DEFLATE compression is used
    - tiling is disabled to avoid block-size errors
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 72)
    print("PROCESSING DEM")
    print("=" * 72)
    print()

    print("Input raster:")
    print(input_raster)
    print()

    # --------------------------------------------------------------
    # OPEN INPUT DEM
    # --------------------------------------------------------------

    with rasterio.open(input_raster) as src:

        print("Raster information:")
        print(
            f"  Width       : {src.width}"
        )

        print(
            f"  Height      : {src.height}"
        )

        print(
            f"  Bands       : {src.count}"
        )

        print(
            f"  CRS         : {src.crs}"
        )

        print(
            f"  Resolution  : {src.res}"
        )

        print(
            f"  NoData      : {src.nodata}"
        )

        print()

        # ----------------------------------------------------------
        # READ FIRST BAND
        # ----------------------------------------------------------

        dem = src.read(1)

        # ----------------------------------------------------------
        # CONVERT TO FLOAT32
        # ----------------------------------------------------------

        dem = dem.astype(
            np.float32,
            copy=False
        )

        # ----------------------------------------------------------
        # HANDLE NODATA
        # ----------------------------------------------------------

        nodata = src.nodata

        if nodata is not None:

            dem[dem == nodata] = np.nan

        # ----------------------------------------------------------
        # REMOVE OBVIOUSLY INVALID ELEVATION VALUES
        #
        # This is only a sanity filter.
        # It does not alter normal DEM elevations.
        # ----------------------------------------------------------

        invalid_mask = (
            (dem < -1000) |
            (dem > 10000)
        )

        dem[invalid_mask] = np.nan

        # ----------------------------------------------------------
        # VALID PIXELS
        # ----------------------------------------------------------

        valid_pixels = dem[
            np.isfinite(dem)
        ]

        if valid_pixels.size == 0:

            raise RuntimeError(
                "No valid elevation pixels were found."
            )

        # ----------------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------------

        minimum = float(
            np.nanmin(dem)
        )

        maximum = float(
            np.nanmax(dem)
        )

        mean = float(
            np.nanmean(dem)
        )

        print("Elevation statistics:")

        print(
            f"  Minimum : {minimum:.2f} m"
        )

        print(
            f"  Maximum : {maximum:.2f} m"
        )

        print(
            f"  Mean    : {mean:.2f} m"
        )

        print()

        # ----------------------------------------------------------
        # OUTPUT PROFILE
        # ----------------------------------------------------------

        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            dtype="float32",
            count=1,
            nodata=np.nan,
            compress="deflate",
            predictor=3,
            tiled=False,
            BIGTIFF="IF_SAFER"
        )

        # ----------------------------------------------------------
        # REMOVE SETTINGS THAT CAN CAUSE BLOCK ERRORS
        # ----------------------------------------------------------

        profile.pop(
            "blockxsize",
            None
        )

        profile.pop(
            "blockysize",
            None
        )

        profile.pop(
            "interleave",
            None
        )

        # ----------------------------------------------------------
        # REMOVE EXISTING OUTPUT
        # ----------------------------------------------------------

        if OUTPUT_FILE.exists():

            print(
                "Existing processed DEM found."
            )

            print(
                "Removing old output..."
            )

            OUTPUT_FILE.unlink()

            print(
                "✓ Old output removed"
            )

            print()

        # ----------------------------------------------------------
        # WRITE OUTPUT
        # ----------------------------------------------------------

        print("Saving processed DEM:")

        print(
            OUTPUT_FILE
        )

        print()

        with rasterio.open(
            OUTPUT_FILE,
            "w",
            **profile
        ) as dst:

            dst.write(
                dem,
                1
            )

    # --------------------------------------------------------------
    # VERIFY OUTPUT
    # --------------------------------------------------------------

    if not OUTPUT_FILE.exists():

        raise RuntimeError(
            "Processed DEM was not created."
        )

    output_size_mb = (
        OUTPUT_FILE.stat().st_size
        / (1024 * 1024)
    )

    print("✓ Processed DEM saved")

    print(
        f"  Size: {output_size_mb:.2f} MB"
    )

    print()


# ----------------------------------------------------------------------
# VERIFY OUTPUT RASTER
# ----------------------------------------------------------------------

def verify_output():
    """
    Re-open the generated GeoTIFF to make sure it is readable.
    """

    print("=" * 72)
    print("VERIFYING PROCESSED DEM")
    print("=" * 72)
    print()

    with rasterio.open(
        OUTPUT_FILE
    ) as src:

        print(
            f"Width       : {src.width}"
        )

        print(
            f"Height      : {src.height}"
        )

        print(
            f"CRS         : {src.crs}"
        )

        print(
            f"Resolution  : {src.res}"
        )

        print(
            f"Data type   : {src.dtypes[0]}"
        )

        print(
            f"Compression : {src.compression}"
        )

        print()

    print(
        "✓ Processed DEM can be opened successfully."
    )

    print()


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():

    print_header()

    # --------------------------------------------------------------
    # CREATE DIRECTORIES
    # --------------------------------------------------------------

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------------
    # FIND ZIP
    # --------------------------------------------------------------

    dem_zip = find_dem_zip()

    if dem_zip is None:

        print(
            "❌ No DEM ZIP found."
        )

        print()

        # Maybe an uncompressed raster already exists.
        existing_raster = find_dem_raster(
            RAW_DIR
        )

        if existing_raster is None:

            print(
                "Expected DEM files inside:"
            )

            print(
                RAW_DIR
            )

            return

        print(
            "Found DEM raster directly:"
        )

        print(
            existing_raster
        )

        print()

        process_dem(
            existing_raster
        )

        verify_output()

        print("=" * 72)
        print("🎉 DEM PROCESSING COMPLETE")
        print("=" * 72)

        return

    # --------------------------------------------------------------
    # ZIP INFORMATION
    # --------------------------------------------------------------

    zip_size_mb = (
        dem_zip.stat().st_size
        / (1024 * 1024)
    )

    print("DEM ZIP FOUND")
    print()

    print("ZIP:")
    print(dem_zip)

    print()

    print(
        f"ZIP size: {zip_size_mb:.2f} MB"
    )

    print()

    # --------------------------------------------------------------
    # TEMPORARY EXTRACTION
    # --------------------------------------------------------------

    print(
        "Creating temporary extraction directory..."
    )

    print()

    extraction_directory = None

    processing_successful = False

    try:

        with tempfile.TemporaryDirectory(
            prefix="dem_extract_",
            dir=RAW_DIR
        ) as temp_directory:

            extraction_directory = Path(
                temp_directory
            )

            print(
                "Temporary directory:"
            )

            print(
                extraction_directory
            )

            print()

            # ------------------------------------------------------
            # EXTRACT ZIP
            # ------------------------------------------------------

            print(
                "Extracting DEM temporarily..."
            )

            print()

            with zipfile.ZipFile(
                dem_zip,
                "r"
            ) as archive:

                archive.extractall(
                    extraction_directory
                )

            print(
                "✓ Extraction complete"
            )

            print()

            # ------------------------------------------------------
            # FIND RASTER
            # ------------------------------------------------------

            dem_raster = find_dem_raster(
                extraction_directory
            )

            if dem_raster is None:

                print(
                    "❌ No DEM raster found inside ZIP."
                )

                print()

                print(
                    "Files found inside ZIP:"
                )

                for file in extraction_directory.rglob("*"):

                    if file.is_file():

                        print(
                            " ",
                            file.relative_to(
                                extraction_directory
                            )
                        )

                raise RuntimeError(
                    "Could not locate DEM raster inside ZIP."
                )

            print(
                "✓ DEM raster found:"
            )

            print(
                dem_raster
            )

            print()

            # ------------------------------------------------------
            # PROCESS
            # ------------------------------------------------------

            process_dem(
                dem_raster
            )

            # ------------------------------------------------------
            # VERIFY
            # ------------------------------------------------------

            verify_output()

            processing_successful = True

        # ----------------------------------------------------------
        # TEMP DIRECTORY AUTOMATICALLY DELETED HERE
        # ----------------------------------------------------------

        print(
            "✓ Temporary extracted files deleted"
        )

        print()

    except Exception:

        print()
        print(
            "❌ DEM processing failed."
        )

        print()

        print(
            "The original ZIP will NOT be deleted."
        )

        print(
            "This protects your downloaded DEM."
        )

        print()

        raise

    # --------------------------------------------------------------
    # DELETE ZIP ONLY AFTER SUCCESS
    # --------------------------------------------------------------

    if processing_successful:

        print(
            "Processing completed successfully."
        )

        print()

        try:

            dem_zip.unlink()

            print(
                "✓ Original DEM ZIP deleted"
            )

            print(
                f"  Freed approximately {zip_size_mb:.2f} MB"
            )

            print()

        except Exception as error:

            print(
                "⚠ Could not delete original DEM ZIP."
            )

            print(
                f"Reason: {error}"
            )

            print()

    # --------------------------------------------------------------
    # FINAL
    # --------------------------------------------------------------

    print("=" * 72)
    print("🎉 DEM PROCESSING COMPLETE")
    print("=" * 72)
    print()

    print("Final processed DEM:")
    print(
        OUTPUT_FILE
    )

    print()

    print("Temporary extraction:")
    print("DELETED")

    print()

    if processing_successful:

        print("Original ZIP:")
        print("DELETED")

    print()

    print("=" * 72)


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()