from pathlib import Path
from datetime import datetime
import json
import re
import sys
from urllib.parse import urljoin

import requests


# ============================================================
# INDIA HYDROLOGY DATA COLLECTOR
# Layer 1: India-wide River Network
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_HYDROLOGY_DIR = PROJECT_ROOT / "data" / "raw" / "hydrology"
RIVERS_DIR = RAW_HYDROLOGY_DIR / "rivers"

METADATA_FILE = RAW_HYDROLOGY_DIR / "hydrology_metadata.json"

DATASET_PAGE = "https://nwdp.nwic.gov.in/dataset/river-line"

REQUEST_TIMEOUT = 30

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
    """Create the required hydrology directories."""

    RIVERS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Hydrology directories ready:")
    print(f"  {RAW_HYDROLOGY_DIR}")
    print(f"  {RIVERS_DIR}")


# ============================================================
# INTERNET / SOURCE CHECK
# ============================================================

def check_dataset_page():
    """
    Download the official NWDP River Network dataset page.

    Returns:
        HTML text if successful, otherwise None.
    """

    print("\nChecking official NWDP website...")

    try:
        response = requests.get(
            DATASET_PAGE,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": USER_AGENT,
            },
        )

        print(
            f"NWDP HTTP status: {response.status_code}"
        )

        response.raise_for_status()

        print("NWDP website is reachable.")

        return response.text

    except requests.RequestException as exc:
        print(
            "\nUnable to reach the NWDP dataset page."
        )
        print(f"Reason: {exc}")

        return None


# ============================================================
# RESOURCE DISCOVERY
# ============================================================

def find_resource_links(html):
    """
    Search the official dataset page for possible
    downloadable River Network resources.

    We do not invent download URLs.
    """

    print(
        "\nSearching official dataset page "
        "for River Network resources..."
    )

    if not html:
        return []

    resource_links = []

    # --------------------------------------------------------
    # Extract normal href links
    # --------------------------------------------------------

    hrefs = re.findall(
        r'href\s*=\s*["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    for href in hrefs:

        absolute_url = urljoin(
            DATASET_PAGE,
            href,
        )

        url_lower = absolute_url.lower()

        # Ignore obvious navigation links.
        if absolute_url.startswith(
            ("javascript:", "mailto:", "#")
        ):
            continue

        # Look for common GIS/download formats.
        if any(
            extension in url_lower
            for extension in (
                ".geojson",
                ".json",
                ".zip",
                ".shp",
                ".kml",
                ".gpkg",
                ".gdb",
                ".csv",
            )
        ):
            if absolute_url not in resource_links:
                resource_links.append(
                    absolute_url
                )

    # --------------------------------------------------------
    # Also inspect HTML for URLs that may be embedded
    # inside JavaScript or page data.
    # --------------------------------------------------------

    url_patterns = re.findall(
        r'https?://[^\s"\'<>]+',
        html,
        flags=re.IGNORECASE,
    )

    for url in url_patterns:

        clean_url = url.rstrip(
            ".,);]}"
        )

        url_lower = clean_url.lower()

        if any(
            extension in url_lower
            for extension in (
                ".geojson",
                ".json",
                ".zip",
                ".shp",
                ".kml",
                ".gpkg",
                ".gdb",
                ".csv",
            )
        ):
            if clean_url not in resource_links:
                resource_links.append(
                    clean_url
                )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique_links = []

    for link in resource_links:

        if link not in unique_links:
            unique_links.append(link)

    print(
        "Potential downloadable resources found: "
        f"{len(unique_links)}"
    )

    if unique_links:

        for index, link in enumerate(
            unique_links,
            start=1,
        ):
            print(
                f"  {index}. {link}"
            )

    else:

        print(
            "No direct GIS download links were exposed "
            "in the page HTML."
        )

    return unique_links


# ============================================================
# SAVE METADATA
# ============================================================

def save_metadata(resource_links):
    """
    Save information about the India hydrology
    data collection process.
    """

    metadata = {
        "project": "Copernicus-India-Flood",
        "collector": "India Hydrology Data Collector",
        "last_checked": datetime.now().isoformat(),
        "source_verified": bool(resource_links),
        "layers": {

            "river_network": {
                "status": (
                    "resources_discovered"
                    if resource_links
                    else "source_reachable_resources_not_found"
                ),
                "name": "River Network",
                "coverage": "India",
                "source": "National Water Data Portal",
                "organization": "Central Water Commission",
                "dataset_page": DATASET_PAGE,
                "target_directory": str(
                    RIVERS_DIR
                ),
                "available_formats": [
                    "GeoJSON",
                    "SHP",
                    "KML",
                    "GeoPackage",
                ],
                "resource_links": resource_links,
            },

            "river_basins": {
                "status": "planned",
            },

            "reservoirs": {
                "status": "planned",
            },

            "surface_waterbodies": {
                "status": "planned",
            },

            "canal_network": {
                "status": "planned",
            },

            "drainage_network": {
                "status": "planned",
            },
        },
    }

    RAW_HYDROLOGY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

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
    print("INDIA HYDROLOGY DATA COLLECTOR")
    print("Layer 1: India-wide River Network")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Create directories
    # --------------------------------------------------------

    create_directories()

    # --------------------------------------------------------
    # 2. Check official source
    # --------------------------------------------------------

    html = check_dataset_page()

    if html is None:

        save_metadata([])

        print("\n" + "=" * 60)
        print("Layer 1 source check failed.")
        print(
            "No data was downloaded."
        )
        print("=" * 60)

        return

    # --------------------------------------------------------
    # 3. Discover resources
    # --------------------------------------------------------

    resource_links = find_resource_links(
        html
    )

    # --------------------------------------------------------
    # 4. Save metadata
    # --------------------------------------------------------

    save_metadata(
        resource_links
    )

    # --------------------------------------------------------
    # 5. Result
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    if resource_links:

        print(
            "Official River Network resources "
            "were discovered."
        )

        print(
            "\nThe discovered resource URLs "
            "were saved to:"
        )

        print(
            METADATA_FILE
        )

        print(
            "\nNext step:"
        )

        print(
            "We will verify the actual GIS resource "
            "before downloading it."
        )

    else:

        print(
            "The official NWDP dataset page is reachable, "
            "but direct GIS download resources were not "
            "exposed in the page HTML."
        )

        print(
            "\nNo guessed or unofficial download URL "
            "was used."
        )

        print(
            "\nNext step:"
        )

        print(
            "We will inspect the official portal/API "
            "resource information."
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
            f"\nCollector failed: {exc}"
        )

        sys.exit(1)