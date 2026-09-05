```python
from pathlib import Path
from datetime import datetime
import json
import re
import sys
import zipfile

import requests


# ============================================================
# INDIA HYDROLOGY MASTER DATA COLLECTOR
# Copernicus-India-Flood
#
# Layer 1: River Network
# Layer 2: River Basins
# Layer 3: Reservoirs and Dams
# Layer 4: Lakes / Surface Water Bodies
# Layer 5: Drainage / Canal Network
#
# CURRENT WORK:
# Layer 3 — India-wide Reservoirs and Dams
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_HYDROLOGY_DIR = (
    PROJECT_ROOT / "data" / "raw" / "hydrology"
)

RIVERS_DIR = RAW_HYDROLOGY_DIR / "rivers"
BASINS_DIR = RAW_HYDROLOGY_DIR / "river_basins"
RESERVOIRS_DIR = RAW_HYDROLOGY_DIR / "reservoirs"
WATER_BODIES_DIR = RAW_HYDROLOGY_DIR / "water_bodies"
DRAINAGE_DIR = RAW_HYDROLOGY_DIR / "drainage"

METADATA_FILE = (
    RAW_HYDROLOGY_DIR / "hydrology_metadata.json"
)

CATALOG_FILE = (
    RAW_HYDROLOGY_DIR / "hydrology_dataset_catalog.json"
)


# ============================================================
# OFFICIAL PORTAL
# ============================================================

NWDP_HOME = "https://nwdp.nwic.gov.in"

RESERVOIR_SEARCH_TERMS = [
    "reservoir",
    "dam",
    "reservoirs",
    "dams",
    "water storage",
    "storage reservoir",
]


# ============================================================
# HTTP SETTINGS
# ============================================================

REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151.0 Safari/537.36"
    )
}


# ============================================================
# DIRECTORIES
# ============================================================

def create_directories():
    """Create all hydrology directories."""

    print("\nCreating hydrology dataset directories...")

    directories = [
        RIVERS_DIR,
        BASINS_DIR,
        RESERVOIRS_DIR,
        WATER_BODIES_DIR,
        DRAINAGE_DIR,
    ]

    names = [
        "Rivers",
        "River Basins",
        "Reservoirs",
        "Water Bodies",
        "Drainage",
    ]

    for directory, name in zip(directories, names):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"  OK: {directory}")


# ============================================================
# EXISTING DATA CHECK
# ============================================================

def list_data_files(directory):
    """Return files already present in a directory."""

    if not directory.exists():
        return []

    return [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and not path.name.endswith(".tmp")
    ]


def check_existing_datasets():
    """Check which hydrology layers are already collected."""

    print("\nChecking existing hydrology datasets...")

    layers = {
        "India-wide River Network": RIVERS_DIR,
        "India-wide River Basins": BASINS_DIR,
        "India-wide Reservoirs and Dams": RESERVOIRS_DIR,
        "India-wide Lakes and Surface Water Bodies": WATER_BODIES_DIR,
        "India-wide Drainage and Canal Network": DRAINAGE_DIR,
    }

    existing = {}

    for name, directory in layers.items():
        files = list_data_files(directory)

        existing[name] = files

        print(
            f"  {name}: {len(files)} file(s)"
        )

    return existing


# ============================================================
# RIVER NETWORK STATUS
# ============================================================

def report_river_network(existing):
    """Report the already collected River Network."""

    files = existing.get(
        "India-wide River Network",
        [],
    )

    print("\n============================================================")
    print("LAYER 1 — RIVER NETWORK")
    print("============================================================")

    if not files:
        print("River Network dataset not found.")
        print("Layer 1 requires collection.")
        return "missing"

    print("Existing River Network found.")

    for file in files:
        size_mb = file.stat().st_size / (
            1024 * 1024
        )

        print(f"File: {file}")
        print(
            f"Size: {size_mb:.2f} MB"
        )

    return "collected"


# ============================================================
# RIVER BASIN STATUS
# ============================================================

def report_river_basins(existing):
    """Report the already collected River Basins."""

    files = existing.get(
        "India-wide River Basins",
        [],
    )

    print("\n============================================================")
    print("LAYER 2 — RIVER BASINS")
    print("============================================================")

    if not files:
        print("River Basin dataset not found.")
        print("Layer 2 requires collection.")
        return "missing"

    print("Existing River Basin dataset found.")

    for file in files:
        size_mb = file.stat().st_size / (
            1024 * 1024
        )

        print(f"File: {file}")
        print(
            f"Size: {size_mb:.2f} MB"
        )

    return "collected"


# ============================================================
# NWDP REQUEST
# ============================================================

def request_nwdp(path="/"):
    """Request a page from the official NWDP portal."""

    url = (
        NWDP_HOME.rstrip("/")
        + "/"
        + path.lstrip("/")
    )

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
        )

        print(
            f"HTTP {response.status_code}: "
            f"{url}"
        )

        if response.ok:
            return response.text

    except requests.RequestException as exc:
        print(
            f"Request failed: {exc}"
        )

    return None


# ============================================================
# RESERVOIR DATASET DISCOVERY
# ============================================================

def discover_reservoir_pages():
    """
    Search the official NWDP portal for reservoir/dam
    dataset pages.

    We do not invent download URLs.
    """

    print(
        "\nSearching official NWDP for Reservoir/Dam data..."
    )

    discovered_pages = []

    # First request the main portal.
    html = request_nwdp("/")

    if html is None:
        return []

    # Search terms are used against the downloaded HTML.
    for term in RESERVOIR_SEARCH_TERMS:

        print(
            f"  Search term: {term}"
        )

        # Search for dataset-style links.
        pattern = re.compile(
            r'href=["\']([^"\']*dataset[^"\']*)["\']',
            re.IGNORECASE,
        )

        matches = pattern.findall(
            html
        )

        for match in matches:

            if term.lower() in (
                match.lower()
            ):

                if match.startswith("/"):
                    full_url = (
                        NWDP_HOME.rstrip("/")
                        + match
                    )

                elif match.startswith("http"):
                    full_url = match

                else:
                    full_url = (
                        NWDP_HOME.rstrip("/")
                        + "/"
                        + match
                    )

                if full_url not in discovered_pages:
                    discovered_pages.append(
                        full_url
                    )

    print(
        "\nPotential dataset pages discovered: "
        f"{len(discovered_pages)}"
    )

    for page in discovered_pages:
        print(f"  {page}")

    return discovered_pages


# ============================================================
# RESOURCE DISCOVERY
# ============================================================

def find_gis_resources(html):
    """
    Find actual GIS download resources exposed directly
    by a dataset page.
    """

    if not html:
        return []

    resources = []

    # Direct href extraction.
    hrefs = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    gis_extensions = (
        ".geojson",
        ".json",
        ".zip",
        ".shp",
        ".kml",
        ".kmz",
        ".gpkg",
    )

    for href in hrefs:

        lower = href.lower()

        if not any(
            extension in lower
            for extension in gis_extensions
        ):
            continue

        if href.startswith("/"):
            url = (
                NWDP_HOME.rstrip("/")
                + href
            )

        elif href.startswith("http"):
            url = href

        else:
            url = (
                NWDP_HOME.rstrip("/")
                + "/"
                + href
            )

        if url not in resources:
            resources.append(url)

    return resources


# ============================================================
# DATASET PAGE INSPECTION
# ============================================================

def inspect_reservoir_pages(pages):
    """Inspect discovered pages for actual GIS resources."""

    all_resources = []

    if not pages:
        return []

    print(
        "\nInspecting discovered Reservoir/Dam "
        "dataset pages..."
    )

    for page in pages:

        print(
            f"\nDataset page:\n{page}"
        )

        try:
            response = requests.get(
                page,
                timeout=REQUEST_TIMEOUT,
                headers=HEADERS,
            )

            print(
                f"HTTP status: "
                f"{response.status_code}"
            )

            if not response.ok:
                continue

            resources = find_gis_resources(
                response.text
            )

            print(
                "GIS resources found: "
                f"{len(resources)}"
            )

            for resource in resources:

                print(
                    f"  {resource}"
                )

                if resource not in all_resources:
                    all_resources.append(
                        resource
                    )

        except requests.RequestException as exc:

            print(
                f"Unable to inspect page: {exc}"
            )

    return all_resources


# ============================================================
# RESOURCE VALIDATION
# ============================================================

def validate_resource(url):
    """
    Verify that the discovered URL actually points to
    a downloadable resource before saving it.
    """

    print(
        "\nVerifying resource:"
    )
    print(url)

    try:

        response = requests.head(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            allow_redirects=True,
        )

        print(
            f"HTTP status: "
            f"{response.status_code}"
        )

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        content_length = response.headers.get(
            "Content-Length",
            "",
        )

        print(
            f"Content-Type: {content_type}"
        )

        if content_length:
            print(
                f"Content-Length: "
                f"{content_length}"
            )

        if response.ok:
            return True

    except requests.RequestException as exc:

        print(
            f"HEAD request failed: {exc}"
        )

    return False


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(url, destination):
    """Download a verified resource."""

    print(
        "\nDownloading official Reservoir/Dam dataset..."
    )

    print(
        f"Source:\n{url}"
    )

    temporary_file = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    try:

        with requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            stream=True,
        ) as response:

            print(
                f"HTTP status: "
                f"{response.status_code}"
            )

            response.raise_for_status()

            total_bytes = 0

            with open(
                temporary_file,
                "wb",
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if not chunk:
                        continue

                    file.write(chunk)
                    total_bytes += len(chunk)

                    if total_bytes % (
                        10 * 1024 * 1024
                    ) < len(chunk):

                        mb = (
                            total_bytes
                            / (1024 * 1024)
                        )

                        print(
                            f"  Downloaded: "
                            f"{mb:.2f} MB"
                        )

        temporary_file.replace(
            destination
        )

        size_mb = (
            destination.stat().st_size
            / (1024 * 1024)
        )

        print(
            f"\nDownloaded size: "
            f"{size_mb:.2f} MB"
        )

        return True

    except Exception as exc:

        print(
            f"\nDownload failed: {exc}"
        )

        if temporary_file.exists():
            temporary_file.unlink()

        return False


# ============================================================
# ZIP VALIDATION
# ============================================================

def inspect_zip(zip_path):
    """Inspect a downloaded ZIP archive."""

    print(
        "\nValidating downloaded ZIP..."
    )

    try:

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as archive:

            members = archive.namelist()

            print(
                f"ZIP contains "
                f"{len(members)} file(s)."
            )

            gis_files = []

            for member in members:

                lower = member.lower()

                if lower.endswith(
                    (
                        ".geojson",
                        ".json",
                        ".shp",
                        ".gpkg",
                        ".kml",
                        ".kmz",
                    )
                ):
                    gis_files.append(
                        member
                    )

            print(
                "\nGIS files discovered:"
            )

            for member in gis_files:
                print(
                    f"  {member}"
                )

            return gis_files

    except zipfile.BadZipFile:

        print(
            "Downloaded file is not a valid ZIP."
        )

    except Exception as exc:

        print(
            f"ZIP inspection failed: {exc}"
        )

    return []


# ============================================================
# RESERVOIR LAYER
# ============================================================

def collect_reservoirs(existing):
    """Collect Layer 3 — Reservoirs and Dams."""

    print("\n============================================================")
    print("LAYER 3 — INDIA-WIDE RESERVOIRS AND DAMS")
    print("============================================================")

    existing_files = existing.get(
        "India-wide Reservoirs and Dams",
        [],
    )

    if existing_files:

        print(
            "Existing Reservoir/Dam data found."
        )

        for file in existing_files:
            size_mb = (
                file.stat().st_size
                / (1024 * 1024)
            )

            print(
                f"File: {file}"
            )

            print(
                f"Size: "
                f"{size_mb:.2f} MB"
            )

        return "collected", None

    pages = discover_reservoir_pages()

    if not pages:

        print(
            "\nNo verified Reservoir/Dam "
            "dataset page was discovered."
        )

        return (
            "source_discovery_completed",
            [],
        )

    resources = inspect_reservoir_pages(
        pages
    )

    if not resources:

        print(
            "\nDataset pages were found, "
            "but no direct GIS resources "
            "were exposed."
        )

        return (
            "source_discovery_completed",
            [],
        )

    print(
        "\nPotential Reservoir/Dam resources:"
    )

    for resource in resources:
        print(
            f"  {resource}"
        )

    # Validate resources before downloading.
    verified = []

    for resource in resources:

        if validate_resource(resource):
            verified.append(resource)

    if not verified:

        print(
            "\nNo downloadable GIS resource "
            "could be verified."
        )

        return (
            "resource_verification_failed",
            resources,
        )

    # Prefer GeoJSON/ZIP GIS resources.
    selected = None

    for resource in verified:

        lower = resource.lower()

        if (
            ".geojson" in lower
            or ".gpkg" in lower
            or ".zip" in lower
            or ".kmz" in lower
            or ".kml" in lower
        ):
            selected = resource
            break

    if selected is None:
        selected = verified[0]

    print(
        "\nSelected verified Reservoir/Dam resource:"
    )
    print(selected)

    # Determine extension.
    lower = selected.lower()

    if ".geojson" in lower:
        filename = "india_reservoirs_dams.geojson"

    elif ".gpkg" in lower:
        filename = "india_reservoirs_dams.gpkg"

    elif ".kmz" in lower:
        filename = "india_reservoirs_dams.kmz"

    elif ".kml" in lower:
        filename = "india_reservoirs_dams.kml"

    else:
        filename = "india_reservoirs_dams.zip"

    destination = (
        RESERVOIRS_DIR / filename
    )

    if destination.exists():

        print(
            "\nDestination already exists:"
        )
        print(destination)

        return (
            "collected",
            selected,
        )

    success = download_file(
        selected,
        destination,
    )

    if not success:
        return (
            "download_failed",
            selected,
        )

    if destination.suffix.lower() == ".zip":

        gis_files = inspect_zip(
            destination
        )

        if not gis_files:

            print(
                "\nWARNING: ZIP downloaded, "
                "but no recognized GIS file "
                "was found inside."
            )

            return (
                "downloaded_validation_pending",
                selected,
            )

    print(
        "\n============================================================"
    )
    print("LAYER 3 — RESERVOIRS / DAMS COMPLETE")
    print("============================================================")

    print(
        "Reservoir/Dam dataset stored at:"
    )
    print(destination)

    return (
        "collected",
        selected,
    )


# ============================================================
# PLACEHOLDER LAYERS
# ============================================================

def report_pending_layers():
    """Report Layers 4 and 5 without downloading anything."""

    print("\n============================================================")
    print("LAYER 4 — INDIA-WIDE LAKES / SURFACE WATER BODIES")
    print("============================================================")

    print(
        "Pending."
    )

    print(
        "\n============================================================"
    )
    print("LAYER 5 — INDIA-WIDE DRAINAGE / CANAL NETWORK")
    print("============================================================")

    print(
        "Pending."
    )


# ============================================================
# CATALOG
# ============================================================

def save_catalog(
    river_status,
    basin_status,
    reservoir_status,
    reservoir_source,
):
    """Save the master hydrology catalog."""

    catalog = {
        "project": "Copernicus-India-Flood",
        "coverage": "India",
        "last_updated": datetime.now().isoformat(),
        "layers": {
            "river_network": {
                "status": river_status,
                "directory": str(
                    RIVERS_DIR
                ),
            },
            "river_basins": {
                "status": basin_status,
                "directory": str(
                    BASINS_DIR
                ),
            },
            "reservoirs_dams": {
                "status": reservoir_status,
                "directory": str(
                    RESERVOIRS_DIR
                ),
                "source": reservoir_source,
            },
            "surface_water_bodies": {
                "status": "pending",
                "directory": str(
                    WATER_BODIES_DIR
                ),
            },
            "drainage_canal_network": {
                "status": "pending",
                "directory": str(
                    DRAINAGE_DIR
                ),
            },
        },
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
        "\nMaster catalog saved to:"
    )
    print(CATALOG_FILE)


# ============================================================
# METADATA
# ============================================================

def save_metadata(
    river_status,
    basin_status,
    reservoir_status,
    reservoir_source,
):
    """Save hydrology metadata."""

    metadata = {
        "project": "Copernicus-India-Flood",
        "coverage": "India",
        "last_updated": datetime.now().isoformat(),
        "layers": {
            "river_network": {
                "status": river_status,
                "directory": str(
                    RIVERS_DIR
                ),
            },
            "river_basins": {
                "status": basin_status,
                "directory": str(
                    BASINS_DIR
                ),
            },
            "reservoirs_dams": {
                "status": reservoir_status,
                "directory": str(
                    RESERVOIRS_DIR
                ),
                "source": reservoir_source,
            },
            "surface_water_bodies": {
                "status": "pending",
                "directory": str(
                    WATER_BODIES_DIR
                ),
            },
            "drainage_canal_network": {
                "status": "pending",
                "directory": str(
                    DRAINAGE_DIR
                ),
            },
        },
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
        "\nMetadata saved to:"
    )
    print(METADATA_FILE)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("INDIA HYDROLOGY MASTER DATA COLLECTOR")
    print("Copernicus-India-Flood")
    print("=" * 60)

    print("\nTarget coverage: INDIA")

    print(
        "\nLayers:"
        "\n  1. India-wide River Network"
        "\n  2. India-wide River Basins"
        "\n  3. India-wide Reservoirs and Dams"
        "\n  4. India-wide Lakes and Surface Water Bodies"
        "\n  5. India-wide Drainage and Canal Network"
    )

    create_directories()

    existing = check_existing_datasets()

    river_status = report_river_network(
        existing
    )

    basin_status = report_river_basins(
        existing
    )

    reservoir_status, reservoir_source = (
        collect_reservoirs(existing)
    )

    report_pending_layers()

    save_catalog(
        river_status,
        basin_status,
        reservoir_status,
        reservoir_source,
    )

    save_metadata(
        river_status,
        basin_status,
        reservoir_status,
        reservoir_source,
    )

    print("\n============================================================")
    print("INDIA HYDROLOGY MASTER COLLECTION STATUS")
    print("============================================================")

    print(
        f"river_network: {river_status}"
    )

    print(
        f"river_basins: {basin_status}"
    )

    print(
        f"reservoirs_dams: {reservoir_status}"
    )

    print(
        "surface_water_bodies: pending"
    )

    print(
        "drainage_canal_network: pending"
    )

    print("\nDirectories:")

    print(
        f"  Rivers:       {RIVERS_DIR}"
    )

    print(
        f"  Basins:       {BASINS_DIR}"
    )

    print(
        f"  Reservoirs:   {RESERVOIRS_DIR}"
    )

    print(
        f"  Water bodies: {WATER_BODIES_DIR}"
    )

    print(
        f"  Drainage:     {DRAINAGE_DIR}"
    )

    print(
        "\n============================================================"
    )

    print(
        "MASTER HYDROLOGY COLLECTION PROGRAM FINISHED."
    )

    print(
        "============================================================"
    )


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
            f"\nCollector failed: {exc}"
        )

        sys.exit(1)
