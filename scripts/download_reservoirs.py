from pathlib import Path
from datetime import datetime
import json
import re
import sys
import zipfile

import requests


# ============================================================
# INDIA HYDROLOGY DATA COLLECTOR
# Layer 3: India-wide Reservoirs
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HYDROLOGY_DIR = PROJECT_ROOT / "data" / "raw" / "hydrology"
RESERVOIR_DIR = HYDROLOGY_DIR / "reservoirs"

METADATA_FILE = HYDROLOGY_DIR / "hydrology_metadata.json"
CATALOG_FILE = HYDROLOGY_DIR / "hydrology_dataset_catalog.json"

DATASET_PAGE = "https://nwdp.nwic.gov.in/dataset/reservoir"

TIMEOUT = 60

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}


# ============================================================
# DIRECTORY SETUP
# ============================================================

def create_directories():
    RESERVOIR_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Reservoir directory ready:")
    print(f"  {RESERVOIR_DIR}")


# ============================================================
# FETCH OFFICIAL DATASET PAGE
# ============================================================

def fetch_dataset_page():
    print("\nChecking official NWDP Reservoir dataset...")

    try:
        response = requests.get(
            DATASET_PAGE,
            headers=HEADERS,
            timeout=TIMEOUT,
        )

        print(f"NWDP HTTP status: {response.status_code}")

        if response.ok:
            print("Official Reservoir dataset page is reachable.")
            return response.text

        print("Official dataset page returned an unexpected status.")

    except requests.RequestException as exc:
        print("Unable to reach official NWDP dataset page:")
        print(exc)

    return None


# ============================================================
# DISCOVER GIS RESOURCES
# ============================================================

def discover_resources(html):
    print("\nSearching official Reservoir resources...")

    hrefs = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    resources = []

    for href in hrefs:
        lower = href.lower()

        if any(
            extension in lower
            for extension in (
                ".geojson",
                ".json",
                ".zip",
                ".shp",
                ".kml",
                ".kmz",
            )
        ):
            if href not in resources:
                resources.append(href)

    print(
        f"Potential official GIS resources found: "
        f"{len(resources)}"
    )

    for resource in resources:
        print(f"  {resource}")

    return resources


# ============================================================
# RESOURCE SELECTION
# ============================================================

def select_resource(resources):
    if not resources:
        return None

    # Prefer GeoJSON ZIP because it preserves GIS attributes
    # while remaining easy to validate with GeoPandas.
    preferred_extensions = [
        ".geojson.zip",
        ".geojson",
        ".zip",
        ".shp.zip",
        ".kml",
        ".kmz",
    ]

    for extension in preferred_extensions:
        for resource in resources:
            if extension in resource.lower():
                return resource

    return resources[0]


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(url):
    print("\nSelected official Reservoir resource:")
    print(url)

    print("\nDownloading official India-wide Reservoir dataset...")

    filename = (
        "india_reservoirs_source"
        + Path(url.split("?")[0]).suffix
    )

    if filename == "india_reservoirs_source":
        filename = "india_reservoirs_source.dat"

    destination = RESERVOIR_DIR / filename

    try:
        with requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            stream=True,
        ) as response:

            print(f"HTTP status: {response.status_code}")

            response.raise_for_status()

            total_bytes = 0

            with open(destination, "wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)
                        total_bytes += len(chunk)

        print(
            "Downloaded size: "
            f"{total_bytes / (1024 * 1024):.2f} MB"
        )

        print(f"\nDownloaded to:")
        print(destination)

        return destination

    except requests.RequestException as exc:
        print("\nDownload failed:")
        print(exc)

        if destination.exists():
            destination.unlink()

        return None


# ============================================================
# ZIP EXTRACTION
# ============================================================

def extract_zip_if_needed(source_file):
    if source_file.suffix.lower() != ".zip":
        return source_file

    print("\nValidating downloaded ZIP...")

    try:
        with zipfile.ZipFile(source_file, "r") as archive:

            members = archive.namelist()

            print(
                f"ZIP contains {len(members)} file(s)."
            )

            gis_members = [
                member
                for member in members
                if member.lower().endswith(
                    (
                        ".geojson",
                        ".json",
                        ".shp",
                        ".gpkg",
                        ".kml",
                        ".kmz",
                    )
                )
            ]

            print("\nGIS files discovered inside ZIP:")

            for member in gis_members:
                print(f"  {member}")

            if not gis_members:
                print(
                    "No supported GIS file was found "
                    "inside the ZIP."
                )
                return None

            extraction_dir = RESERVOIR_DIR / "extracted"

            extraction_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            archive.extractall(extraction_dir)

            print("\nExtracted to:")
            print(extraction_dir)

            for member in gis_members:

                candidate = (
                    extraction_dir / member
                )

                if candidate.exists():
                    return candidate

    except zipfile.BadZipFile:
        print("Downloaded file is not a valid ZIP.")
        return None

    except Exception as exc:
        print("ZIP extraction failed:")
        print(exc)
        return None

    return None


# ============================================================
# GIS VALIDATION
# ============================================================

def validate_gis(gis_file):
    print("\nValidating Reservoir GIS dataset...")

    try:
        import geopandas as gpd

        # Read only the first few rows first.
        sample = gpd.read_file(
            gis_file,
            rows=5,
        )

        print(f"GIS file selected:")
        print(gis_file)

        print(f"\nCRS:")
        print(sample.crs)

        print("\nColumns:")

        for column in sample.columns:
            print(f"  {column}")

        print("\nGeometry types:")

        if "geometry" in sample.columns:
            print(
                sample.geometry.geom_type.value_counts()
            )

        # Full feature count.
        full = gpd.read_file(gis_file)

        print(
            f"\nFeature count: {len(full)}"
        )

        if full.empty:
            print(
                "ERROR: Reservoir dataset contains "
                "zero features."
            )
            return None

        geometry_valid = (
            full.geometry.notna().all()
        )

        print(
            "Geometry values present:",
            geometry_valid,
        )

        if not geometry_valid:
            print(
                "WARNING: Some features have missing geometry."
            )

        print("\nGIS validation successful.")

        return {
            "feature_count": int(len(full)),
            "crs": str(full.crs),
            "columns": [
                str(column)
                for column in full.columns
            ],
            "geometry_types": {
                str(key): int(value)
                for key, value in (
                    full.geometry.geom_type
                    .value_counts()
                    .to_dict()
                    .items()
                )
            },
        }

    except Exception as exc:
        print("\nGIS validation failed:")
        print(exc)
        return None


# ============================================================
# METADATA UPDATE
# ============================================================

def update_metadata(
    source_url,
    local_file,
    validation,
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

    metadata.setdefault(
        "project",
        "Copernicus-India-Flood",
    )

    metadata["last_updated"] = (
        datetime.now().isoformat()
    )

    metadata.setdefault(
        "layers",
        {},
    )

    metadata["layers"]["reservoirs"] = {
        "status": "collected",
        "name": "India-wide Reservoirs",
        "coverage": "India",
        "source": "National Water Data Portal",
        "organization": "Central Water Commission",
        "dataset_page": DATASET_PAGE,
        "source_url": source_url,
        "local_file": str(local_file),
        "downloaded_at": datetime.now().isoformat(),
        "validation": validation,
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

    print("\nMetadata updated:")
    print(METADATA_FILE)


# ============================================================
# MASTER CATALOG UPDATE
# ============================================================

def update_catalog(
    source_url,
    local_file,
    validation,
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

    catalog.setdefault(
        "project",
        "Copernicus-India-Flood",
    )

    catalog.setdefault(
        "coverage",
        "India",
    )

    catalog.setdefault(
        "datasets",
        {},
    )

    catalog["datasets"]["reservoirs"] = {
        "status": "collected",
        "layer": "Reservoirs",
        "coverage": "India",
        "source": "National Water Data Portal",
        "organization": "Central Water Commission",
        "dataset_page": DATASET_PAGE,
        "source_url": source_url,
        "local_file": str(local_file),
        "feature_count": validation[
            "feature_count"
        ],
        "crs": validation["crs"],
        "geometry_types": validation[
            "geometry_types"
        ],
        "columns": validation["columns"],
    }

    catalog["last_updated"] = (
        datetime.now().isoformat()
    )

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

    print("\nMaster catalog updated:")
    print(CATALOG_FILE)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("INDIA HYDROLOGY DATA COLLECTOR")
    print("Layer 3: India-wide Reservoirs")
    print("=" * 60)

    create_directories()

    html = fetch_dataset_page()

    if html is None:
        print("\nReservoir collection stopped.")
        return

    resources = discover_resources(html)

    if not resources:
        print(
            "\nNo official GIS Reservoir resource "
            "was discovered."
        )
        print(
            "We will not guess a download URL."
        )
        return

    selected_resource = select_resource(
        resources
    )

    if selected_resource is None:
        print(
            "\nUnable to select an official "
            "Reservoir resource."
        )
        return

    source_file = download_file(
        selected_resource
    )

    if source_file is None:
        return

    gis_file = extract_zip_if_needed(
        source_file
    )

    if gis_file is None:
        print(
            "\nCould not identify a valid GIS "
            "dataset."
        )
        return

    validation = validate_gis(
        gis_file
    )

    if validation is None:
        print(
            "\nReservoir GIS validation failed."
        )
        return

    update_metadata(
        selected_resource,
        gis_file,
        validation,
    )

    update_catalog(
        selected_resource,
        gis_file,
        validation,
    )

    print("\n" + "=" * 60)
    print("LAYER 3 — RESERVOIRS COMPLETE")
    print("=" * 60)

    print("\nIndia-wide Reservoir dataset:")
    print(gis_file)

    print(
        f"\nFeature count: "
        f"{validation['feature_count']}"
    )

    print(
        "\nNext layer:"
    )
    print(
        "Layer 4 — India-wide Dams"
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