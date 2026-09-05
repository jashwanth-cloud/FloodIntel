"""
======================================================================
INDIA HYDROLOGY DATA DOWNLOADER
Layer 4: Surface Waterbodies
======================================================================

Official source:
National Water Data Portal (NWDP)
National Water Informatics Centre (NWIC)
Ministry of Jal Shakti
Dataset publisher: Space Applications Centre (SAC), ISRO

Dataset:
Surface Waterbodies

Description:
State-wise waterbody boundaries for area > 0.1 hectare,
extracted from satellite imagery.

This program:

1. Downloads the official NWDP Surface Waterbodies page
2. Discovers state/UT waterbody resources automatically
3. Selects GeoJSON resources only
4. Downloads the official ZIP files
5. Extracts GeoJSON
6. Validates every dataset
7. Rejects obvious wrong/admin datasets
8. Adds source_state
9. Merges all valid datasets
10. Creates an India-wide GeoJSON
11. Generates validation + metadata reports

IMPORTANT:
This program does NOT use search-engine results.
It discovers resources directly from the official NWDP page.
======================================================================
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, unquote

import requests


# ======================================================================
# CONFIGURATION
# ======================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

HYDROLOGY_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "hydrology"
)

OUTPUT_DIR = (
    HYDROLOGY_DIR
    / "water_bodies"
)

RAW_DIR = (
    OUTPUT_DIR
    / "raw_downloads"
)

STATE_DIR = (
    OUTPUT_DIR
    / "states"
)

FINAL_DIR = (
    OUTPUT_DIR
    / "final"
)

REPORT_DIR = (
    OUTPUT_DIR
    / "reports"
)

PAGE_CACHE = (
    OUTPUT_DIR
    / "nwdp_surface_waterbodies.html"
)

FINAL_GEOJSON = (
    FINAL_DIR
    / "india_surface_waterbodies.geojson"
)

STATE_INDEX = (
    REPORT_DIR
    / "surface_waterbodies_state_index.json"
)

VALIDATION_REPORT = (
    REPORT_DIR
    / "surface_waterbodies_validation.json"
)

METADATA_FILE = (
    REPORT_DIR
    / "surface_waterbodies_metadata.json"
)

CATALOG_FILE = (
    HYDROLOGY_DIR
    / "hydrology_dataset_catalog.json"
)

NWDP_URL = (
    "https://nwdp.nwic.gov.in/dataset/surface-waterbodies"
)

# The NWDP page currently exposes 30+ state/UT resources.
# We don't hard-code resource UUIDs.
# This list is ONLY used to report missing expected regions.
EXPECTED_REGIONS = [
    "Andaman And Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Chandigarh",
    "Daman & Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Jharkhand",
    "Jammu And Kashmir",
    "Kerala",
    "Lakshadweep",
    "Ladakh",
    "Maharashtra",
    "Meghalaya",
    "Manipur",
    "Madhya Pradesh",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Puducherry",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Tripura",
    "Telangana",
    "Uttarakhand",
    "Uttar Pradesh",
    "West Bengal",
]


# ======================================================================
# HTTP SESSION
# ======================================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
    }
)


# ======================================================================
# UTILITIES
# ======================================================================

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_filename(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_text(value: str) -> str:
    value = html.unescape(value)
    value = unquote(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def sha256_file(path: Path) -> str:

    digest = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def ensure_directories():

    for directory in [
        OUTPUT_DIR,
        RAW_DIR,
        STATE_DIR,
        FINAL_DIR,
        REPORT_DIR,
    ]:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


# ======================================================================
# DOWNLOAD OFFICIAL PAGE
# ======================================================================

def download_official_page() -> str:

    print()
    print("=" * 72)
    print("STEP 1 — OFFICIAL NWDP PAGE")
    print("=" * 72)

    response = SESSION.get(
        NWDP_URL,
        timeout=90,
    )

    print(
        f"HTTP status: {response.status_code}"
    )

    response.raise_for_status()

    page = response.text

    PAGE_CACHE.write_text(
        page,
        encoding="utf-8",
    )

    print(
        f"Page downloaded: "
        f"{len(page):,} bytes"
    )

    return page


# ======================================================================
# RESOURCE DISCOVERY
# ======================================================================

def discover_resources(page: str) -> list[dict]:
    """
    Discover actual resource blocks from the NWDP HTML.

    We intentionally do NOT guess UUIDs.

    A valid resource must contain:
        title="Waterbody <region>"
        data-format="geojson"
        download URL containing:
        /resource/<UUID>/download/
    """

    print()
    print("=" * 72)
    print("STEP 2 — DISCOVER OFFICIAL GEOJSON RESOURCES")
    print("=" * 72)

    resources = []

    # ------------------------------------------------------------------
    # Strategy A:
    # Find resource blocks by their heading links.
    # ------------------------------------------------------------------

    heading_pattern = re.compile(
        r'<a\s+class=["\']heading["\']'
        r'[^>]*'
        r'href=["\']([^"\']+/resource/[^"\']+)["\']'
        r'[^>]*'
        r'title=["\']([^"\']+)["\']'
        r'[^>]*>'
        r'(.*?)'
        r'</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    headings = list(
        heading_pattern.finditer(page)
    )

    print(
        f"Resource heading candidates: "
        f"{len(headings)}"
    )

    for match in headings:

        resource_page_url = (
            urljoin(
                NWDP_URL,
                match.group(1),
            )
        )

        title = normalize_text(
            match.group(2)
        )

        block_start = match.start()

        # Resource blocks on the NWDP page are fairly large.
        # Search until the next heading or a reasonable boundary.
        next_heading = page.find(
            '<a class="heading"',
            match.end(),
        )

        if next_heading == -1:
            block_end = min(
                len(page),
                match.end() + 12000,
            )
        else:
            block_end = next_heading

        block = page[
            block_start:block_end
        ]

        # Only Waterbody resources.
        if not re.search(
            r"\bWaterbody\b",
            title,
            flags=re.IGNORECASE,
        ):
            continue

        # Must explicitly say GeoJSON.
        if not re.search(
            r'data-format=["\']geojson["\']',
            block,
            flags=re.IGNORECASE,
        ):
            continue

        # Find download URL.
        download_matches = re.findall(
            r'href=["\']([^"\']+)["\']',
            block,
            flags=re.IGNORECASE,
        )

        download_url = None

        for candidate in download_matches:

            candidate_full = urljoin(
                NWDP_URL,
                candidate,
            )

            lower = candidate_full.lower()

            if (
                "/download/" in lower
                and (
                    "geojson" in lower
                    or lower.endswith(".geojson")
                )
            ):
                download_url = candidate_full
                break

        if not download_url:
            continue

        # Extract resource UUID.
        uuid_match = re.search(
            r"/resource/"
            r"([0-9a-f-]{36})",
            download_url,
            flags=re.IGNORECASE,
        )

        if not uuid_match:
            continue

        resource_id = uuid_match.group(1)

        # Extract region.
        region_match = re.search(
            r"Waterbody\s+(.+)$",
            title,
            flags=re.IGNORECASE,
        )

        if not region_match:
            continue

        region = normalize_text(
            region_match.group(1)
        )

        resource = {
            "region": region,
            "title": title,
            "resource_id": resource_id,
            "resource_page": resource_page_url,
            "download_url": download_url,
            "format": "GeoJSON",
        }

        resources.append(resource)

    # ------------------------------------------------------------------
    # Deduplicate by region.
    # ------------------------------------------------------------------

    unique = {}

    for resource in resources:

        key = safe_filename(
            resource["region"]
        )

        # Keep first valid GeoJSON resource.
        if key not in unique:
            unique[key] = resource

    resources = list(
        unique.values()
    )

    resources.sort(
        key=lambda x: x["region"].lower()
    )

    print(
        f"Valid GeoJSON waterbody resources: "
        f"{len(resources)}"
    )

    for resource in resources:

        print(
            f"  ✓ {resource['region']}"
        )

    return resources


# ======================================================================
# DOWNLOAD RESOURCE
# ======================================================================

def download_resource(
    resource: dict,
) -> Path | None:

    region = resource["region"]

    filename = (
        f"{safe_filename(region)}"
        "_surface_waterbodies.zip"
    )

    destination = (
        RAW_DIR
        / filename
    )

    print()
    print(
        f"[{region}]"
    )

    print(
        f"  Resource ID: "
        f"{resource['resource_id']}"
    )

    print(
        f"  URL: "
        f"{resource['download_url']}"
    )

    try:

        response = SESSION.get(
            resource["download_url"],
            timeout=300,
            stream=True,
        )

        print(
            f"  HTTP status: "
            f"{response.status_code}"
        )

        response.raise_for_status()

        total = 0

        with open(
            destination,
            "wb",
        ) as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024,
            ):

                if chunk:

                    f.write(chunk)

                    total += len(chunk)

        print(
            f"  Downloaded: "
            f"{total / (1024 * 1024):.2f} MB"
        )

        if total == 0:

            print(
                "  ✗ Empty download"
            )

            destination.unlink(
                missing_ok=True
            )

            return None

        return destination

    except Exception as exc:

        print(
            f"  ✗ DOWNLOAD FAILED: {exc}"
        )

        destination.unlink(
            missing_ok=True
        )

        return None


# ======================================================================
# ZIP EXTRACTION
# ======================================================================

def extract_geojson(
    zip_path: Path,
    region: str,
) -> Path | None:

    region_dir = (
        STATE_DIR
        / safe_filename(region)
    )

    if region_dir.exists():
        shutil.rmtree(
            region_dir
        )

    region_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"  Extracting..."
    )

    try:

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as archive:

            members = archive.namelist()

            geojson_members = [
                member
                for member in members
                if member.lower().endswith(
                    (
                        ".geojson",
                        ".json",
                    )
                )
            ]

            if not geojson_members:

                print(
                    "  ✗ ZIP contains no "
                    "GeoJSON/JSON file"
                )

                return None

            # Prefer explicit GeoJSON.
            geojson_members.sort(
                key=lambda x: (
                    not x.lower().endswith(
                        ".geojson"
                    ),
                    len(x),
                )
            )

            selected = geojson_members[0]

            print(
                f"  Selected: {selected}"
            )

            archive.extract(
                selected,
                region_dir,
            )

        extracted = (
            region_dir
            / selected
        )

        # ZIP paths may contain nested folders.
        if not extracted.exists():

            matches = list(
                region_dir.rglob(
                    Path(selected).name
                )
            )

            if matches:
                extracted = matches[0]

        if not extracted.exists():

            print(
                "  ✗ Extracted file not found"
            )

            return None

        return extracted

    except zipfile.BadZipFile:

        print(
            "  ✗ Download is not a valid ZIP"
        )

        return None

    except Exception as exc:

        print(
            f"  ✗ Extraction failed: {exc}"
        )

        return None


# ======================================================================
# GEOJSON VALIDATION
# ======================================================================

def validate_geojson(
    path: Path,
    region: str,
) -> dict:

    result = {
        "region": region,
        "file": str(path),
        "valid_json": False,
        "feature_collection": False,
        "feature_count": 0,
        "geometry_count": 0,
        "null_geometry_count": 0,
        "coordinate_samples": 0,
        "coordinate_range_valid": True,
        "suspicious_admin_fields": [],
        "status": "FAILED",
        "reason": None,
    }

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        result["valid_json"] = True

    except Exception as exc:

        result["reason"] = (
            f"Invalid JSON: {exc}"
        )

        return result

    if data.get("type") != "FeatureCollection":

        result["reason"] = (
            "GeoJSON is not a FeatureCollection"
        )

        return result

    result["feature_collection"] = True

    features = data.get(
        "features",
        [],
    )

    if not isinstance(
        features,
        list,
    ):

        result["reason"] = (
            "features is not a list"
        )

        return result

    result["feature_count"] = len(
        features
    )

    if len(features) == 0:

        result["reason"] = (
            "Zero features"
        )

        return result

    # --------------------------------------------------------------
    # Inspect geometries and properties.
    # --------------------------------------------------------------

    suspicious_fields = set()

    admin_field_keywords = {
        "village",
        "vill_name",
        "village_name",
        "tehsil",
        "taluk",
        "block",
        "district",
        "panchayat",
        "admin",
        "boundary",
    }

    def inspect_coordinates(
        coordinates,
    ):

        if not isinstance(
            coordinates,
            list,
        ):
            return

        # Leaf coordinate pair.
        if (
            len(coordinates) >= 2
            and isinstance(
                coordinates[0],
                (int, float),
            )
            and isinstance(
                coordinates[1],
                (int, float),
            )
        ):

            lon = coordinates[0]
            lat = coordinates[1]

            result["coordinate_samples"] += 1

            # WGS84 geographic range.
            if not (
                -180 <= lon <= 180
                and -90 <= lat <= 90
            ):

                result[
                    "coordinate_range_valid"
                ] = False

            return

        for child in coordinates:

            inspect_coordinates(
                child
            )

    for feature in features:

        if not isinstance(
            feature,
            dict,
        ):
            continue

        geometry = feature.get(
            "geometry"
        )

        if geometry is None:

            result[
                "null_geometry_count"
            ] += 1

        else:

            result[
                "geometry_count"
            ] += 1

            coordinates = geometry.get(
                "coordinates"
            )

            if coordinates is not None:

                inspect_coordinates(
                    coordinates
                )

        properties = (
            feature.get(
                "properties"
            )
            or {}
        )

        for field in properties.keys():

            field_lower = str(
                field
            ).lower()

            for keyword in admin_field_keywords:

                if keyword in field_lower:

                    suspicious_fields.add(
                        field
                    )

    result[
        "suspicious_admin_fields"
    ] = sorted(
        suspicious_fields
    )

    # --------------------------------------------------------------
    # Validation decisions.
    # --------------------------------------------------------------

    if result["geometry_count"] == 0:

        result["reason"] = (
            "No geometries found"
        )

        return result

    if not result[
        "coordinate_range_valid"
    ]:

        result["reason"] = (
            "Invalid geographic coordinate range"
        )

        return result

    # Waterbody datasets can legitimately contain
    # district/village-related attributes, so we DO NOT
    # reject merely because a district field exists.
    #
    # Instead, source identity + resource title + geometry
    # are the primary checks.

    result["status"] = "VALID"

    return result


# ======================================================================
# ADD SOURCE STATE
# ======================================================================

def load_geojson(path: Path) -> dict:

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def add_source_state(
    data: dict,
    region: str,
) -> dict:

    for feature in data.get(
        "features",
        [],
    ):

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            properties = {}

        properties[
            "source_state"
        ] = region

        properties[
            "source_dataset"
        ] = "NWDP Surface Waterbodies"

        properties[
            "source_publisher"
        ] = "Space Applications Centre (ISRO)"

        feature[
            "properties"
        ] = properties

    return data


# ======================================================================
# MERGE DATASETS
# ======================================================================

def merge_datasets(
    validated: list[dict],
) -> dict:

    print()
    print("=" * 72)
    print("STEP 4 — MERGING INDIA-WIDE DATASET")
    print("=" * 72)

    merged_features = []

    for item in validated:

        path = Path(
            item["file"]
        )

        region = item[
            "region"
        ]

        print(
            f"  Merging {region}..."
        )

        data = load_geojson(
            path
        )

        data = add_source_state(
            data,
            region,
        )

        merged_features.extend(
            data.get(
                "features",
                [],
            )
        )

    merged = {
        "type": "FeatureCollection",
        "name": (
            "India Surface Waterbodies "
            "(NWDP / SAC-ISRO)"
        ),
        "features": merged_features,
    }

    return merged


# ======================================================================
# FINAL VALIDATION
# ======================================================================

def validate_final(
    merged: dict,
) -> dict:

    features = merged.get(
        "features",
        [],
    )

    regions = set()

    geometry_count = 0

    null_geometry_count = 0

    for feature in features:

        properties = (
            feature.get(
                "properties"
            )
            or {}
        )

        state = properties.get(
            "source_state"
        )

        if state:
            regions.add(
                state
            )

        if feature.get(
            "geometry"
        ) is None:

            null_geometry_count += 1

        else:

            geometry_count += 1

    expected = {
        safe_filename(x)
        for x in EXPECTED_REGIONS
    }

    actual = {
        safe_filename(x)
        for x in regions
    }

    missing_expected = sorted(
        expected - actual
    )

    unexpected = sorted(
        actual - expected
    )

    report = {
        "timestamp_utc": now_utc(),
        "dataset": (
            "India Surface Waterbodies"
        ),
        "source": NWDP_URL,
        "publisher": (
            "Space Applications Centre (ISRO)"
        ),
        "feature_count": len(
            features
        ),
        "geometry_count": geometry_count,
        "null_geometry_count": (
            null_geometry_count
        ),
        "regions_found": sorted(
            regions
        ),
        "region_count": len(
            regions
        ),
        "expected_region_count": len(
            EXPECTED_REGIONS
        ),
        "missing_expected_regions": (
            missing_expected
        ),
        "unexpected_regions": (
            unexpected
        ),
        "status": (
            "VALID"
            if (
                len(features) > 0
                and geometry_count > 0
            )
            else "FAILED"
        ),
    }

    return report


# ======================================================================
# SAVE JSON
# ======================================================================

def save_json(
    path: Path,
    data,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ======================================================================
# UPDATE HYDROLOGY CATALOG
# ======================================================================

def update_catalog(
    final_report: dict,
):

    catalog = {}

    if CATALOG_FILE.exists():

        try:

            catalog = json.loads(
                CATALOG_FILE.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            catalog = {}

    catalog[
        "layer_4_surface_waterbodies"
    ] = {
        "status": (
            "complete"
            if final_report["status"]
            == "VALID"
            else "validation_failed"
        ),
        "dataset": (
            "Surface Waterbodies"
        ),
        "publisher": (
            "Space Applications Centre (ISRO)"
        ),
        "portal": (
            "National Water Data Portal"
        ),
        "source_url": NWDP_URL,
        "format": "GeoJSON",
        "coverage": (
            "State/UT resources merged "
            "into India-wide FeatureCollection"
        ),
        "feature_count": (
            final_report[
                "feature_count"
            ]
        ),
        "region_count": (
            final_report[
                "region_count"
            ]
        ),
        "final_file": str(
            FINAL_GEOJSON
        ),
        "last_validated_utc": (
            now_utc()
        ),
    }

    save_json(
        CATALOG_FILE,
        catalog,
    )


# ======================================================================
# MAIN
# ======================================================================

def main():

    print()
    print("=" * 72)
    print("INDIA HYDROLOGY DATA DOWNLOADER")
    print("LAYER 4 — SURFACE WATERBODIES")
    print("=" * 72)

    print()
    print(
        "Project:"
    )
    print(
        PROJECT_ROOT
    )

    print()
    print(
        "Official source:"
    )
    print(
        NWDP_URL
    )

    ensure_directories()

    # --------------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------------

    page = download_official_page()

    # --------------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------------

    resources = discover_resources(
        page
    )

    if not resources:

        print()
        print(
            "❌ STOPPED"
        )
        print(
            "No official GeoJSON waterbody "
            "resources were discovered."
        )

        print()
        print(
            "No dataset was downloaded."
        )

        sys.exit(1)

    # --------------------------------------------------------------
    # STEP 3
    # Download + extract + validate
    # --------------------------------------------------------------

    print()
    print("=" * 72)
    print("STEP 3 — DOWNLOAD + EXTRACT + VALIDATE")
    print("=" * 72)

    validated = []

    failed = []

    for index, resource in enumerate(
        resources,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(resources)}] "
            f"{resource['region']}"
        )

        zip_path = download_resource(
            resource
        )

        if zip_path is None:

            failed.append(
                {
                    "region": resource[
                        "region"
                    ],
                    "reason": (
                        "Download failed"
                    ),
                }
            )

            continue

        extracted = extract_geojson(
            zip_path,
            resource["region"],
        )

        if extracted is None:

            failed.append(
                {
                    "region": resource[
                        "region"
                    ],
                    "reason": (
                        "GeoJSON extraction failed"
                    ),
                }
            )

            continue

        validation = validate_geojson(
            extracted,
            resource["region"],
        )

        print(
            f"  Features: "
            f"{validation['feature_count']:,}"
        )

        print(
            f"  Geometries: "
            f"{validation['geometry_count']:,}"
        )

        if validation[
            "status"
        ] != "VALID":

            print(
                f"  ❌ INVALID: "
                f"{validation['reason']}"
            )

            failed.append(
                {
                    "region": resource[
                        "region"
                    ],
                    "reason": validation[
                        "reason"
                    ],
                }
            )

            continue

        print(
            "  ✅ VALID WATERBODY DATA"
        )

        validated.append(
            {
                "region": resource[
                    "region"
                ],
                "file": str(
                    extracted
                ),
                "resource_id": resource[
                    "resource_id"
                ],
                "resource_page": resource[
                    "resource_page"
                ],
                "download_url": resource[
                    "download_url"
                ],
                "feature_count": validation[
                    "feature_count"
                ],
                "geometry_count": validation[
                    "geometry_count"
                ],
                "sha256": sha256_file(
                    extracted
                ),
            }
        )

        time.sleep(0.5)

    # --------------------------------------------------------------
    # State index
    # --------------------------------------------------------------

    save_json(
        STATE_INDEX,
        {
            "timestamp_utc": now_utc(),
            "source": NWDP_URL,
            "resources_discovered": len(
                resources
            ),
            "resources_validated": len(
                validated
            ),
            "resources_failed": len(
                failed
            ),
            "validated": validated,
            "failed": failed,
        },
    )

    # --------------------------------------------------------------
    # Must have at least one valid dataset.
    # --------------------------------------------------------------

    if not validated:

        print()
        print(
            "❌ NO VALID WATERBODY DATASETS"
        )

        print(
            "Layer 4 is NOT complete."
        )

        sys.exit(2)

    # --------------------------------------------------------------
    # STEP 4 — Merge
    # --------------------------------------------------------------

    merged = merge_datasets(
        validated
    )

    # --------------------------------------------------------------
    # STEP 5 — Final validation
    # --------------------------------------------------------------

    print()
    print("=" * 72)
    print("STEP 5 — FINAL INDIA-WIDE VALIDATION")
    print("=" * 72)

    final_report = validate_final(
        merged
    )

    print()
    print(
        f"Total features: "
        f"{final_report['feature_count']:,}"
    )

    print(
        f"Total geometries: "
        f"{final_report['geometry_count']:,}"
    )

    print(
        f"Regions found: "
        f"{final_report['region_count']}"
    )

    if final_report[
        "missing_expected_regions"
    ]:

        print()
        print(
            "⚠ Expected regions not found:"
        )

        for region in final_report[
            "missing_expected_regions"
        ]:

            print(
                f"  - {region}"
            )

    # --------------------------------------------------------------
    # Save merged dataset.
    # --------------------------------------------------------------

    print()
    print(
        "Writing final GeoJSON..."
    )

    save_json(
        FINAL_GEOJSON,
        merged,
    )

    # Save validation report.
    save_json(
        VALIDATION_REPORT,
        final_report,
    )

    # Metadata.
    metadata = {
        "dataset": (
            "India Surface Waterbodies"
        ),
        "source": NWDP_URL,
        "publisher": (
            "Space Applications Centre (ISRO)"
        ),
        "department": (
            "National Water Informatics Centre"
        ),
        "min_area_hectare": 0.1,
        "source_description": (
            "State wise waterbody boundaries "
            "for area more than 0.1 hectare. "
            "Extracted from Satellite imagery."
        ),
        "format": "GeoJSON",
        "created_utc": now_utc(),
        "final_file": str(
            FINAL_GEOJSON
        ),
        "feature_count": (
            final_report[
                "feature_count"
            ]
        ),
        "region_count": (
            final_report[
                "region_count"
            ]
        ),
    }

    save_json(
        METADATA_FILE,
        metadata,
    )

    # Update master catalog.
    update_catalog(
        final_report
    )

    # --------------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------------

    print()
    print("=" * 72)
    print("LAYER 4 — FINAL RESULT")
    print("=" * 72)

    if final_report[
        "status"
    ] == "VALID":

        print()
        print(
            "🌊 LAYER 4 VALIDATION PASSED"
        )

        print()
        print(
            "India-wide Surface Waterbodies:"
        )

        print(
            f"  Features : "
            f"{final_report['feature_count']:,}"
        )

        print(
            f"  Regions  : "
            f"{final_report['region_count']}"
        )

        print()
        print(
            "Final dataset:"
        )

        print(
            FINAL_GEOJSON
        )

        print()
        print(
            "Validation report:"
        )

        print(
            VALIDATION_REPORT
        )

        print()
        print(
            "Metadata:"
        )

        print(
            METADATA_FILE
        )

        print()
        print(
            "✅ Layer 4 is ready for the flood model."
        )

    else:

        print()
        print(
            "⚠ LAYER 4 IS NOT COMPLETE."
        )

        print(
            "Review the validation report:"
        )

        print(
            VALIDATION_REPORT
        )

        sys.exit(3)

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()