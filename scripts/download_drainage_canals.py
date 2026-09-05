from pathlib import Path
from datetime import datetime
import json
import sys
import zipfile

import requests
import geopandas as gpd


# ============================================================
# INDIA HYDROLOGY DATA COLLECTOR
# LAYER 5: INDIA-WIDE CANAL / DRAINAGE NETWORK
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HYDROLOGY_DIR = PROJECT_ROOT / "data" / "raw" / "hydrology"
DRAINAGE_DIR = HYDROLOGY_DIR / "drainage"

METADATA_FILE = HYDROLOGY_DIR / "hydrology_metadata.json"
CATALOG_FILE = HYDROLOGY_DIR / "hydrology_dataset_catalog.json"

DATASET_PAGE = "https://nwdp.nwic.gov.in/dataset/canal"

REQUEST_TIMEOUT = 120

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "Chrome/151.0 Safari/537.36"
)


# ============================================================
# DIRECTORIES
# ============================================================

def create_directories():
    DRAINAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Drainage / Canal directory ready:")
    print(f"  {DRAINAGE_DIR}")


# ============================================================
# DATASET PAGE
# ============================================================

def get_dataset_page():
    print("\nChecking official NWDP Canal Network dataset...")

    try:
        response = requests.get(
            DATASET_PAGE,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": USER_AGENT,
            },
        )

        print(f"NWDP HTTP status: {response.status_code}")

        if response.ok:
            print("Official Canal Network dataset page is reachable.")
            return response.text

        print(
            "NWDP returned HTTP status "
            f"{response.status_code}"
        )

    except requests.RequestException as exc:
        print("Unable to reach NWDP:")
        print(exc)

    return None


# ============================================================
# RESOURCE DISCOVERY
# ============================================================

def find_resources(html):
    """
    Find official GIS download resources exposed by the
    NWDP Canal Network dataset page.
    """

    import re

    print("\nSearching official Canal Network resources...")

    hrefs = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    resources = []

    for href in hrefs:

        href_lower = href.lower()

        if (
            ".geojson" in href_lower
            or ".zip" in href_lower
            or ".kml" in href_lower
            or ".shp" in href_lower
        ):
            if href not in resources:
                resources.append(href)

    print(
        "Potential official GIS resources found: "
        f"{len(resources)}"
    )

    for resource in resources:
        print(f"  {resource}")

    return resources


# ============================================================
# SELECT RESOURCE
# ============================================================

def select_resource(resources):
    """
    Prefer GeoJSON, then SHP ZIP, then KML.
    """

    if not resources:
        return None

    geojson_resources = [
        r for r in resources
        if ".geojson" in r.lower()
    ]

    if geojson_resources:
        return geojson_resources[0]

    shp_resources = [
        r for r in resources
        if ".zip" in r.lower()
    ]

    if shp_resources:
        return shp_resources[0]

    kml_resources = [
        r for r in resources
        if ".kml" in r.lower()
    ]

    if kml_resources:
        return kml_resources[0]

    return resources[0]


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(url, destination):
    print("\nDownloading official India-wide Canal Network...")
    print("Source:")
    print(url)

    try:
        with requests.get(
            url,
            stream=True,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": USER_AGENT,
            },
        ) as response:

            print(
                f"HTTP status: {response.status_code}"
            )

            response.raise_for_status()

            total_bytes = 0

            with open(destination, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if not chunk:
                        continue

                    file.write(chunk)
                    total_bytes += len(chunk)

            size_mb = total_bytes / (1024 * 1024)

            print(
                f"Downloaded size: {size_mb:.2f} MB"
            )

        return True

    except requests.RequestException as exc:
        print("\nDownload failed:")
        print(exc)

        if destination.exists():
            destination.unlink()

        return False


# ============================================================
# VALIDATE GEOJSON
# ============================================================

def validate_geojson(path):
    print("\nValidating Canal Network GeoJSON...")

    try:
        gdf = gpd.read_file(
            path,
            rows=5,
        )

        print(
            f"CRS: {gdf.crs}"
        )

        print("Columns:")

        for column in gdf.columns:
            print(f"  {column}")

        print(
            "\nSample records successfully read."
        )

        return True

    except Exception as exc:
        print(
            "\nGeoJSON validation failed:"
        )
        print(exc)

        return False


# ============================================================
# VALIDATE ZIP
# ============================================================

def validate_zip(path):
    print("\nValidating downloaded ZIP...")

    try:
        with zipfile.ZipFile(path, "r") as archive:

            names = archive.namelist()

            print(
                f"ZIP contains {len(names)} file(s)."
            )

            gis_files = [
                name
                for name in names
                if name.lower().endswith(
                    (
                        ".shp",
                        ".geojson",
                        ".json",
                        ".kml",
                    )
                )
            ]

            print("\nGIS files discovered:")

            for name in gis_files:
                print(f"  {name}")

            if not gis_files:
                print(
                    "No GIS dataset found inside ZIP."
                )
                return False

        return True

    except zipfile.BadZipFile:
        print(
            "Downloaded file is not a valid ZIP."
        )
        return False

    except Exception as exc:
        print(
            "ZIP validation failed:"
        )
        print(exc)
        return False


# ============================================================
# SAVE METADATA
# ============================================================

def update_metadata(
    resource_url,
    downloaded_file,
    status,
):
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

    metadata["project"] = "Copernicus-India-Flood"
    metadata["last_updated"] = datetime.now().isoformat()

    if "layers" not in metadata:
        metadata["layers"] = {}

    metadata["layers"]["canal_network"] = {
        "status": status,
        "name": "India-wide Canal / Drainage Network",
        "coverage": "India",
        "source": "National Water Data Portal",
        "organization": "Central Water Commission",
        "dataset_page": DATASET_PAGE,
        "resource_url": resource_url,
        "downloaded_file": str(downloaded_file),
        "collected_at": datetime.now().isoformat(),
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
# UPDATE MASTER CATALOG
# ============================================================

def update_catalog(
    resource_url,
    downloaded_file,
    status,
):
    catalog = {}

    if CATALOG_FILE.exists():
        try:
            with open(
                CATALOG_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                catalog = json.load(file)
        except Exception:
            catalog = {}

    catalog["project"] = "Copernicus-India-Flood"
    catalog["last_updated"] = datetime.now().isoformat()

    if "layers" not in catalog:
        catalog["layers"] = {}

    catalog["layers"]["drainage"] = {
        "status": status,
        "dataset": "India-wide Canal Network",
        "source": "National Water Data Portal",
        "organization": "Central Water Commission",
        "dataset_page": DATASET_PAGE,
        "resource_url": resource_url,
        "downloaded_file": str(downloaded_file),
    }

    with open(
        CATALOG_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            catalog,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        "\nMaster catalog updated:"
    )
    print(CATALOG_FILE)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("INDIA HYDROLOGY DATA DOWNLOADER")
    print("Layer 5: India-wide Canal / Drainage Network")
    print("=" * 60)

    create_directories()

    html = get_dataset_page()

    if html is None:
        update_metadata(
            "",
            "",
            "source_unreachable",
        )

        print("\nLayer 5 could not be collected.")
        return

    resources = find_resources(html)

    resource_url = select_resource(resources)

    if resource_url is None:

        update_metadata(
            "",
            "",
            "resources_not_found",
        )

        print(
            "\nNo official GIS resource was found."
        )

        return

    print("\nSelected official resource:")
    print(resource_url)

    extension = ".geojson"

    if ".zip" in resource_url.lower():
        extension = ".zip"

    elif ".kml" in resource_url.lower():
        extension = ".kml"

    output_file = (
        DRAINAGE_DIR
        / f"india_canal_network{extension}"
    )

    success = download_file(
        resource_url,
        output_file,
    )

    if not success:
        update_metadata(
            resource_url,
            output_file,
            "download_failed",
        )
        return

    valid = True

    if extension == ".geojson":
        valid = validate_geojson(
            output_file
        )

    elif extension == ".zip":
        valid = validate_zip(
            output_file
        )

    if not valid:

        update_metadata(
            resource_url,
            output_file,
            "downloaded_validation_failed",
        )

        print(
            "\nLayer 5 validation failed."
        )

        return

    update_metadata(
        resource_url,
        output_file,
        "collected",
    )

    update_catalog(
        resource_url,
        output_file,
        "collected",
    )

    print("\n" + "=" * 60)
    print("LAYER 5 — CANAL / DRAINAGE NETWORK COMPLETE")
    print("=" * 60)

    print(
        "\nIndia-wide Canal Network dataset:"
    )

    print(output_file)

    print(
        "\nThis layer is now stored in the "
        "hydrology dataset collection."
    )

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print(
            "\nCollector stopped by user."
        )
        sys.exit(1)

    except Exception as exc:
        print(
            "\nCollector failed:"
        )
        print(exc)
        sys.exit(1)