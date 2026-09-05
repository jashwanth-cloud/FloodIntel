from pathlib import Path
import json
import sys

import requests


# ============================================================
# INDIA HYDROLOGY DATA DOWNLOADER
# Layer 1: India-wide River Network
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_HYDROLOGY_DIR = PROJECT_ROOT / "data" / "raw" / "hydrology"
RIVERS_DIR = RAW_HYDROLOGY_DIR / "rivers"

METADATA_FILE = RAW_HYDROLOGY_DIR / "hydrology_metadata.json"

OUTPUT_FILE = RIVERS_DIR / "india_river_network.geojson"

DOWNLOAD_URL = (
    "https://nwdp.nwic.gov.in/dataset/"
    "3209962f-d0ff-45b8-910a-209bf69a0ccf/resource/"
    "6e552705-842d-40a4-92b2-8506bb66df2a/download/"
    "river_network.geojson"
)

REQUEST_TIMEOUT = 120


# ============================================================
# DIRECTORIES
# ============================================================

def create_directories():
    """Create the required output directories."""

    RIVERS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("River Network directory:")
    print(f"  {RIVERS_DIR}")


# ============================================================
# DOWNLOAD
# ============================================================

def download_river_network():
    """Download the official India-wide River Network GeoJSON."""

    print("\nDownloading official India-wide River Network...")
    print("Source:")
    print(DOWNLOAD_URL)

    try:
        response = requests.get(
            DOWNLOAD_URL,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/151.0 Safari/537.36"
                )
            },
        )

        print(
            f"\nHTTP status: {response.status_code}"
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "unknown",
        )

        print(
            f"Content-Type: {content_type}"
        )

        file_size_mb = (
            len(response.content) / (1024 * 1024)
        )

        print(
            f"Downloaded size: {file_size_mb:.2f} MB"
        )

        if not response.content:
            raise RuntimeError(
                "Downloaded file is empty."
            )

        with open(
            OUTPUT_FILE,
            "wb",
        ) as file:
            file.write(response.content)

        print(
            "\nRiver Network downloaded successfully:"
        )
        print(OUTPUT_FILE)

        return True

    except requests.RequestException as exc:
        print(
            "\nDownload failed:"
        )
        print(exc)
        return False

    except OSError as exc:
        print(
            "\nUnable to save the downloaded file:"
        )
        print(exc)
        return False


# ============================================================
# GEOJSON VALIDATION
# ============================================================

def validate_geojson():
    """Validate that the downloaded file is valid GeoJSON."""

    print("\nValidating downloaded GeoJSON...")

    try:
        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "GeoJSON root is not an object."
            )

        geojson_type = data.get(
            "type"
        )

        print(
            f"GeoJSON type: {geojson_type}"
        )

        if geojson_type not in (
            "FeatureCollection",
            "Feature",
        ):
            raise ValueError(
                "Downloaded file does not appear "
                "to be valid GeoJSON."
            )

        if geojson_type == "FeatureCollection":

            features = data.get(
                "features",
                [],
            )

            print(
                f"Feature count: {len(features)}"
            )

        print(
            "GeoJSON validation successful."
        )

        return True

    except json.JSONDecodeError as exc:
        print(
            "\nThe downloaded file is not valid JSON:"
        )
        print(exc)
        return False

    except Exception as exc:
        print(
            "\nGeoJSON validation failed:"
        )
        print(exc)
        return False


# ============================================================
# UPDATE METADATA
# ============================================================

def update_metadata():
    """Update hydrology metadata with download information."""

    metadata = {}

    if METADATA_FILE.exists():

        try:
            with open(
                METADATA_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                metadata = json.load(file)

        except Exception:
            metadata = {}

    metadata.setdefault(
        "project",
        "Copernicus-India-Flood",
    )

    metadata.setdefault(
        "layers",
        {},
    )

    metadata["layers"]["river_network"] = {
        "status": "downloaded",
        "name": "India-wide River Network",
        "coverage": "India",
        "source": "National Water Data Portal",
        "organization": "Central Water Commission",
        "dataset_page": (
            "https://nwdp.nwic.gov.in/dataset/"
            "river-line"
        ),
        "format": "GeoJSON",
        "download_url": DOWNLOAD_URL,
        "local_file": str(
            OUTPUT_FILE
        ),
        "validated": True,
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        "\nMetadata updated:"
    )
    print(METADATA_FILE)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("INDIA HYDROLOGY DATA DOWNLOADER")
    print("Layer 1: India-wide River Network")
    print("=" * 60)

    create_directories()

    if not download_river_network():
        sys.exit(1)

    if not validate_geojson():
        sys.exit(1)

    update_metadata()

    print("\n" + "=" * 60)
    print("LAYER 1 COMPLETE")
    print("=" * 60)

    print(
        "\nOfficial India-wide River Network data is now stored at:"
    )
    print(OUTPUT_FILE)

    print(
        "\nNext step:"
    )
    print(
        "Inspect the river network attributes and geometry "
        "before moving to Layer 2."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print(
            "\nDownload stopped by user."
        )
        sys.exit(1)

    except Exception as exc:
        print(
            f"\nDownloader failed: {exc}"
        )
        sys.exit(1)