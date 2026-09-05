from pathlib import Path
from datetime import datetime
import json
import sys
import zipfile
import re
from html import unescape

import requests


# ============================================================
# INDIA HYDROLOGY DATA COLLECTOR
# Layer 2: India-wide River Basins
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HYDROLOGY_DIR = PROJECT_ROOT / "data" / "raw" / "hydrology"

BASINS_DIR = HYDROLOGY_DIR / "river_basins"

METADATA_FILE = HYDROLOGY_DIR / "hydrology_metadata.json"

CATALOG_FILE = HYDROLOGY_DIR / "hydrology_dataset_catalog.json"


# ============================================================
# OFFICIAL NWDP DATASET
# ============================================================

DATASET_PAGE = "https://nwdp.nwic.gov.in/dataset/basin-cwc"

REQUEST_TIMEOUT = 60

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "Chrome/151.0 Safari/537.36"
)


# ============================================================
# DIRECTORIES
# ============================================================

def create_directories():
    """Create the India-wide river basin directory."""

    BASINS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("River Basin directory ready:")
    print(f"  {BASINS_DIR}")


# ============================================================
# HTTP SESSION
# ============================================================

def create_session():
    """Create a requests session."""

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        }
    )

    return session


# ============================================================
# DATASET PAGE
# ============================================================

def get_dataset_page(session):
    """Download the official NWDP Basin dataset page."""

    print("\nChecking official NWDP Basin dataset...")

    response = session.get(
        DATASET_PAGE,
        timeout=REQUEST_TIMEOUT,
    )

    print(
        f"NWDP HTTP status: {response.status_code}"
    )

    response.raise_for_status()

    print("Official Basin dataset page is reachable.")

    return response.text


# ============================================================
# RESOURCE DISCOVERY
# ============================================================

def discover_resources(html):
    """
    Discover GIS download resources from the official
    NWDP Basin dataset page.
    """

    print("\nSearching for official Basin resources...")

    html = unescape(html)

    hrefs = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    resources = []

    for href in hrefs:

        href_lower = href.lower()

        is_download = "download/" in href_lower

        is_gis = any(
            extension in href_lower
            for extension in (
                ".zip",
                ".geojson",
                ".json",
                ".kml",
                ".kmz",
                ".shp",
            )
        )

        if is_download and is_gis:

            if href.startswith("/"):
                href = (
                    "https://nwdp.nwic.gov.in"
                    + href
                )

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
# SELECT BEST RESOURCE
# ============================================================

def select_resource(resources):
    """
    Prefer GeoJSON ZIP, then SHP ZIP,
    then other GIS formats.
    """

    if not resources:
        return None

    priority = [
        ".geojson.zip",
        "geojson",
        ".shp.zip",
        "shape",
        ".shp",
        ".kmz",
        ".kml",
    ]

    for preferred in priority:

        for resource in resources:

            if preferred in resource.lower():
                return resource

    return resources[0]


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(
    session,
    url,
    output_path,
):
    """Download the official basin resource."""

    print(
        "\nDownloading official "
        "India-wide River Basins..."
    )

    print("Source:")
    print(url)

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    with session.get(
        url,
        stream=True,
        timeout=REQUEST_TIMEOUT,
    ) as response:

        print(
            f"HTTP status: {response.status_code}"
        )

        response.raise_for_status()

        total_bytes = 0

        with open(
            temporary_path,
            "wb",
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if not chunk:
                    continue

                file.write(chunk)

                total_bytes += len(chunk)

                if (
                    total_bytes
                    % (50 * 1024 * 1024)
                ) < len(chunk):

                    downloaded_mb = (
                        total_bytes
                        / (1024 * 1024)
                    )

                    print(
                        "Downloaded: "
                        f"{downloaded_mb:.2f} MB"
                    )

    temporary_path.replace(output_path)

    final_size_mb = (
        output_path.stat().st_size
        / (1024 * 1024)
    )

    print(
        "\nDownloaded size: "
        f"{final_size_mb:.2f} MB"
    )

    return output_path


# ============================================================
# ZIP VALIDATION
# ============================================================

def validate_zip(zip_path):

    print("\nValidating downloaded ZIP...")

    if not zipfile.is_zipfile(zip_path):

        raise ValueError(
            "Downloaded file is not "
            "a valid ZIP archive."
        )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        members = archive.namelist()

    print(
        f"ZIP contains {len(members)} file(s)."
    )

    gis_files = [
        name
        for name in members
        if name.lower().endswith(
            (
                ".shp",
                ".geojson",
                ".json",
                ".kml",
                ".kmz",
                ".dbf",
                ".shx",
                ".prj",
            )
        )
    ]

    print(
        "\nGIS files discovered inside ZIP:"
    )

    for name in gis_files:
        print(f"  {name}")

    if not gis_files:

        raise ValueError(
            "No recognizable GIS files "
            "were found inside the ZIP."
        )

    return members


# ============================================================
# EXTRACT
# ============================================================

def extract_zip(
    zip_path,
    destination,
):
    """Extract the official basin dataset."""

    print("\nExtracting Basin dataset...")

    extract_dir = destination / "extracted"

    extract_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        archive.extractall(
            extract_dir
        )

    print(
        "Extracted to:"
    )
    print(extract_dir)

    return extract_dir


# ============================================================
# GIS VALIDATION
# ============================================================

def validate_gis(extracted_dir):

    print("\nValidating GIS dataset...")

    try:

        import geopandas as gpd

    except ImportError:

        print(
            "GeoPandas is not available."
        )

        return None

    candidates = []

    candidates.extend(
        extracted_dir.rglob("*.shp")
    )

    candidates.extend(
        extracted_dir.rglob("*.geojson")
    )

    candidates.extend(
        extracted_dir.rglob("*.json")
    )

    if not candidates:

        print(
            "No directly readable vector "
            "GIS file was found."
        )

        return None

    selected = candidates[0]

    print(
        "GIS file selected:"
    )
    print(selected)

    gdf = gpd.read_file(
        selected
    )

    print(
        f"\nFeature count: {len(gdf)}"
    )

    print(
        f"CRS: {gdf.crs}"
    )

    print("\nColumns:")

    for column in gdf.columns:
        print(f"  {column}")

    print("\nGeometry types:")

    print(
        gdf.geometry.geom_type.value_counts()
    )

    if gdf.crs is None:

        print(
            "\nWARNING: CRS is missing."
        )

    else:

        print(
            "\nGIS validation successful."
        )

    return {
        "file": str(selected),
        "feature_count": int(len(gdf)),
        "crs": str(gdf.crs),
        "columns": [
            str(column)
            for column in gdf.columns
        ],
        "geometry_types": {
            str(key): int(value)
            for key, value
            in gdf.geometry.geom_type.value_counts().items()
        },
    }


# ============================================================
# UPDATE METADATA
# ============================================================

def update_metadata(
    resource_url,
    downloaded_file,
    validation,
):
    """Update project hydrology metadata."""

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

    metadata["project"] = (
        "Copernicus-India-Flood"
    )

    metadata["last_updated"] = (
        datetime.now().isoformat()
    )

    metadata.setdefault(
        "layers",
        {}
    )

    metadata["layers"]["river_basins"] = {

        "status": "collected",

        "name": (
            "India-wide River Basins"
        ),

        "coverage": "India",

        "source": (
            "National Water Data Portal"
        ),

        "organization": (
            "Central Water Commission"
        ),

        "dataset_page": DATASET_PAGE,

        "resource_url": resource_url,

        "downloaded_file": str(
            downloaded_file
        ),

        "validation": validation,

        "collection_date": (
            datetime.now().isoformat()
        ),
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
    validation,
):
    """Update the master hydrology catalog."""

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

    catalog["project"] = (
        "Copernicus-India-Flood"
    )

    catalog["coverage"] = "India"

    catalog["last_updated"] = (
        datetime.now().isoformat()
    )

    catalog.setdefault(
        "datasets",
        {}
    )

    catalog["datasets"]["river_basins"] = {

        "status": "collected",

        "source": (
            "National Water Data Portal"
        ),

        "organization": (
            "Central Water Commission"
        ),

        "dataset_page": DATASET_PAGE,

        "resource_url": resource_url,

        "local_file": str(
            downloaded_file
        ),

        "validation": validation,
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
    print(
        "INDIA HYDROLOGY DATA DOWNLOADER"
    )
    print(
        "Layer 2: India-wide River Basins"
    )
    print("=" * 60)

    create_directories()

    session = create_session()

    html = get_dataset_page(
        session
    )

    resources = discover_resources(
        html
    )

    resource_url = select_resource(
        resources
    )

    if not resource_url:

        raise RuntimeError(
            "No official Basin GIS resource "
            "was discovered."
        )

    print(
        "\nSelected official resource:"
    )
    print(resource_url)

    output_zip = (
        BASINS_DIR
        / "india_river_basins.zip"
    )

    if output_zip.exists():

        print(
            "\nExisting Basin ZIP found."
        )

        print(
            f"File: {output_zip}"
        )

    else:

        download_file(
            session,
            resource_url,
            output_zip,
        )

    validate_zip(
        output_zip
    )

    extracted_dir = extract_zip(
        output_zip,
        BASINS_DIR,
    )

    validation = validate_gis(
        extracted_dir
    )

    update_metadata(
        resource_url,
        output_zip,
        validation,
    )

    update_catalog(
        resource_url,
        output_zip,
        validation,
    )

    print("\n" + "=" * 60)
    print(
        "LAYER 2 — RIVER BASINS COMPLETE"
    )
    print("=" * 60)

    print(
        "\nIndia-wide River Basin dataset:"
    )

    print(output_zip)

    print(
        "\nThe original downloaded archive "
        "has been preserved."
    )

    print(
        "\nNext layer:"
    )

    print(
        "Layer 3 — India-wide Reservoirs "
        "and Dams"
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