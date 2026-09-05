from pathlib import Path
import json
import shutil
import sys

import geopandas as gpd
import pandas as pd


# ============================================================
# INDIA FLOOD PROJECT
# LAYER 4 — SURFACE WATERBODIES
#
# Purpose:
#   Process already-downloaded official NWDP waterbody GeoJSONs
#   State by state, using the CRS embedded in each file.
#
# Output CRS:
#   EPSG:4326
#
# IMPORTANT:
#   This script DOES NOT download anything.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "hydrology"
    / "water_bodies"
    / "states"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "hydrology"
    / "water_bodies"
    / "processed"
)

FINAL_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "hydrology"
    / "water_bodies"
    / "india"
)

FINAL_FILE = FINAL_DIR / "india_surface_waterbodies.geojson"

TARGET_CRS = "EPSG:4326"


# ============================================================
# STATE DIRECTORY → OFFICIAL STATE NAME
# ============================================================

STATE_NAMES = {
    "andaman_and_nicobar_islands": "Andaman And Nicobar Islands",
    "andhra_pradesh": "Andhra Pradesh",
    "arunachal_pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chandigarh": "Chandigarh",
    "chhattisgarh": "Chhattisgarh",
    "daman_and_diu": "Daman & Diu",
    "delhi": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "jammu_and_kashmir": "Jammu And Kashmir",
    "jharkhand": "Jharkhand",
    "kerala": "Kerala",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "madhya_pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "puducherry": "Puducherry",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil_nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar_pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west_bengal": "West Bengal",
}


# ============================================================
# HELPERS
# ============================================================

def print_header(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def find_geojson(state_dir):
    """
    Find the actual waterbody GeoJSON inside a state's directory.

    We deliberately avoid blindly selecting unrelated GeoJSON files.
    Prefer filenames beginning with wb_sac_.
    """

    candidates = list(state_dir.rglob("*.GeoJSON"))
    candidates += list(state_dir.rglob("*.geojson"))

    if not candidates:
        return None

    preferred = [
        p for p in candidates
        if p.name.lower().startswith("wb_sac_")
    ]

    if preferred:
        return preferred[0]

    return candidates[0]


def read_source_crs(path):
    """
    Read CRS directly from GeoJSON metadata.

    Example:
        urn:ogc:def:crs:EPSG::7755
    """

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    crs = data.get("crs")

    if not crs:
        return None

    properties = crs.get("properties", {})

    crs_name = properties.get("name")

    if not crs_name:
        return None

    # Convert:
    # urn:ogc:def:crs:EPSG::7755
    # →
    # EPSG:7755

    if "EPSG::" in crs_name:
        epsg_code = crs_name.split("EPSG::")[-1]
        return f"EPSG:{epsg_code}"

    if "EPSG:" in crs_name:
        return crs_name

    return crs_name


def validate_coordinates(gdf):
    """
    Validate ONLY after reprojection to EPSG:4326.
    """

    if gdf.empty:
        return False, "Dataset is empty."

    if gdf.crs is None:
        return False, "CRS is missing."

    if str(gdf.crs).upper() != TARGET_CRS:
        return False, f"Unexpected CRS: {gdf.crs}"

    bounds = gdf.total_bounds

    minx, miny, maxx, maxy = bounds

    if not all(pd.notna(v) for v in bounds):
        return False, "Bounds contain NaN."

    if minx < -180 or maxx > 180:
        return False, (
            f"Longitude outside range: "
            f"{minx:.6f} to {maxx:.6f}"
        )

    if miny < -90 or maxy > 90:
        return False, (
            f"Latitude outside range: "
            f"{miny:.6f} to {maxy:.6f}"
        )

    return True, (
        f"Bounds OK: "
        f"{minx:.4f}, {miny:.4f}, "
        f"{maxx:.4f}, {maxy:.4f}"
    )


def geometry_statistics(gdf):
    """
    Calculate basic geometry statistics useful for validation.
    """

    geometry_types = (
        gdf.geometry
        .geom_type
        .value_counts()
        .to_dict()
    )

    invalid_count = int((~gdf.geometry.is_valid).sum())

    empty_count = int(gdf.geometry.is_empty.sum())

    return geometry_types, invalid_count, empty_count


# ============================================================
# MAIN
# ============================================================

def main():

    print_header(
        "INDIA HYDROLOGY PROCESSOR\n"
        "LAYER 4 — SURFACE WATERBODIES"
    )

    print(f"Project root:")
    print(f"  {PROJECT_ROOT}")

    print()
    print(f"Input:")
    print(f"  {INPUT_ROOT}")

    print()
    print(f"Output:")
    print(f"  {FINAL_FILE}")

    print()
    print("Target CRS:")
    print(f"  {TARGET_CRS}")

    if not INPUT_ROOT.exists():
        print()
        print("ERROR:")
        print("Waterbody state directory does not exist.")
        sys.exit(1)

    # --------------------------------------------------------
    # Discover state directories
    # --------------------------------------------------------

    state_dirs = sorted(
        [p for p in INPUT_ROOT.iterdir() if p.is_dir()]
    )

    print()
    print(f"State directories discovered: {len(state_dirs)}")

    if not state_dirs:
        print("ERROR: No state datasets found.")
        sys.exit(1)

    # --------------------------------------------------------
    # Prepare directories
    # --------------------------------------------------------

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    processed_files = []
    failed_states = []

    total_features = 0

    # --------------------------------------------------------
    # Process one state at a time
    # --------------------------------------------------------

    for index, state_dir in enumerate(state_dirs, start=1):

        state_key = state_dir.name.lower()

        state_name = STATE_NAMES.get(
            state_key,
            state_dir.name.replace("_", " ").title()
        )

        print()
        print("-" * 72)
        print(f"[{index}/{len(state_dirs)}] {state_name}")
        print("-" * 72)

        source_file = find_geojson(state_dir)

        if source_file is None:

            print("  ❌ No GeoJSON found.")

            failed_states.append({
                "state": state_name,
                "reason": "No GeoJSON found"
            })

            continue

        print(f"  Source:")
        print(f"    {source_file}")

        try:

            # ------------------------------------------------
            # Read CRS directly from original GeoJSON
            # ------------------------------------------------

            source_crs = read_source_crs(source_file)

            print(f"  Source CRS:")
            print(f"    {source_crs}")

            if source_crs is None:
                raise ValueError(
                    "Source GeoJSON does not contain CRS metadata."
                )

            # ------------------------------------------------
            # Read GeoDataFrame
            # ------------------------------------------------

            print("  Reading dataset...")

            gdf = gpd.read_file(source_file)

            original_count = len(gdf)

            print(f"  Features:")
            print(f"    {original_count:,}")

            if original_count == 0:
                raise ValueError("Dataset contains zero features.")

            # ------------------------------------------------
            # Confirm source CRS
            # ------------------------------------------------

            if gdf.crs is None:

                print(
                    "  GeoPandas CRS missing; "
                    f"assigning source CRS {source_crs}"
                )

                gdf = gdf.set_crs(
                    source_crs,
                    allow_override=True
                )

            else:

                print(f"  GeoPandas CRS:")
                print(f"    {gdf.crs}")

            # ------------------------------------------------
            # Reproject
            # ------------------------------------------------

            print("  Reprojecting → EPSG:4326...")

            gdf = gdf.to_crs(TARGET_CRS)

            print(f"  Output CRS:")
            print(f"    {gdf.crs}")

            # ------------------------------------------------
            # Geometry cleanup
            # ------------------------------------------------

            empty_before = int(gdf.geometry.is_empty.sum())

            if empty_before > 0:

                print(
                    f"  Removing empty geometries: "
                    f"{empty_before:,}"
                )

                gdf = gdf[
                    ~gdf.geometry.is_empty
                ].copy()

            # ------------------------------------------------
            # Geometry validity
            # ------------------------------------------------

            invalid_count = int(
                (~gdf.geometry.is_valid).sum()
            )

            if invalid_count > 0:

                print(
                    f"  Fixing invalid geometries: "
                    f"{invalid_count:,}"
                )

                gdf["geometry"] = (
                    gdf.geometry.make_valid()
                )

            # ------------------------------------------------
            # Add provenance fields
            # ------------------------------------------------

            gdf["source_state"] = state_name
            gdf["source_dataset"] = "NWDP Surface Waterbodies"
            gdf["source_crs"] = source_crs

            # ------------------------------------------------
            # Coordinate validation AFTER reprojection
            # ------------------------------------------------

            valid, message = validate_coordinates(gdf)

            if not valid:
                raise ValueError(message)

            print(f"  ✓ {message}")

            # ------------------------------------------------
            # Geometry statistics
            # ------------------------------------------------

            geometry_types, invalid_after, empty_after = (
                geometry_statistics(gdf)
            )

            print("  Geometry types:")
            for geom_type, count in geometry_types.items():
                print(f"    {geom_type}: {count:,}")

            print(
                f"  Invalid geometries remaining: "
                f"{invalid_after:,}"
            )

            print(
                f"  Empty geometries remaining: "
                f"{empty_after:,}"
            )

            if invalid_after > 0:
                raise ValueError(
                    "Invalid geometries remain after cleanup."
                )

            # ------------------------------------------------
            # Save processed state
            # ------------------------------------------------

            state_output_dir = OUTPUT_ROOT / state_key

            state_output_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            output_file = (
                state_output_dir
                / f"{state_key}_surface_waterbodies.geojson"
            )

            print("  Saving processed dataset...")

            gdf.to_file(
                output_file,
                driver="GeoJSON"
            )

            print(f"  ✓ Saved:")
            print(f"    {output_file}")

            processed_files.append(output_file)

            total_features += len(gdf)

            print(
                f"  ✓ STATE COMPLETE — "
                f"{len(gdf):,} features"
            )

        except Exception as exc:

            print()
            print(f"  ❌ FAILED: {exc}")

            failed_states.append({
                "state": state_name,
                "source_file": str(source_file),
                "reason": str(exc)
            })

    # ========================================================
    # NATIONAL MERGE
    # ========================================================

    print_header(
        "MERGING PROCESSED SURFACE WATERBODY DATASETS"
    )

    print(
        f"Successfully processed states: "
        f"{len(processed_files)}"
    )

    print(
        f"Failed states: "
        f"{len(failed_states)}"
    )

    if not processed_files:

        print()
        print("❌ NO VALID DATASETS WERE PROCESSED.")
        sys.exit(1)

    print()
    print(
        "WARNING: National merge can require significant RAM "
        "because the dataset contains hundreds of thousands "
        "of polygons."
    )

    print()
    print("Reading processed state datasets...")

    frames = []

    for path in processed_files:

        print(f"  Loading: {path.name}")

        gdf = gpd.read_file(path)

        frames.append(gdf)

    print()
    print("Concatenating...")

    combined = gpd.GeoDataFrame(
        pd.concat(
            frames,
            ignore_index=True
        ),
        crs=TARGET_CRS
    )

    # --------------------------------------------------------
    # Final national validation
    # --------------------------------------------------------

    print()
    print("Final validation...")

    print(
        f"Total features: "
        f"{len(combined):,}"
    )

    print(
        f"CRS: "
        f"{combined.crs}"
    )

    valid, message = validate_coordinates(combined)

    if not valid:

        print(f"❌ FINAL VALIDATION FAILED: {message}")

        sys.exit(1)

    print(f"✓ {message}")

    invalid_final = int(
        (~combined.geometry.is_valid).sum()
    )

    empty_final = int(
        combined.geometry.is_empty.sum()
    )

    print(
        f"Invalid geometries: "
        f"{invalid_final:,}"
    )

    print(
        f"Empty geometries: "
        f"{empty_final:,}"
    )

    if invalid_final > 0 or empty_final > 0:

        print(
            "❌ Final geometry validation failed."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Save national dataset
    # --------------------------------------------------------

    print()
    print("Saving India-wide dataset...")

    combined.to_file(
        FINAL_FILE,
        driver="GeoJSON"
    )

    print()
    print("=" * 72)
    print("🎉 LAYER 4 — SURFACE WATERBODIES COMPLETE")
    print("=" * 72)

    print()
    print("India-wide dataset:")
    print(f"  {FINAL_FILE}")

    print()
    print("CRS:")
    print(f"  {combined.crs}")

    print()
    print("Total features:")
    print(f"  {len(combined):,}")

    print()
    print("Source:")
    print("  Official NWDP Surface Waterbodies")

    # --------------------------------------------------------
    # Save processing report
    # --------------------------------------------------------

    report = {
        "layer": 4,
        "name": "Surface Waterbodies",
        "source": "NWDP",
        "target_crs": TARGET_CRS,
        "states_discovered": len(state_dirs),
        "states_processed": len(processed_files),
        "states_failed": len(failed_states),
        "total_features": len(combined),
        "final_file": str(FINAL_FILE),
        "failed_states": failed_states,
    }

    report_file = FINAL_DIR / "layer4_processing_report.json"

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=2
        )

    print()
    print("Processing report:")
    print(f"  {report_file}")

    print()
    print("=" * 72)

    if failed_states:

        print(
            "⚠️ WARNING: Some states failed processing."
        )

        for item in failed_states:
            print(
                f"  - {item['state']}: "
                f"{item['reason']}"
            )

    else:

        print(
            "✅ ALL DISCOVERED WATERBODY DATASETS "
            "PROCESSED SUCCESSFULLY."
        )

    print("=" * 72)


if __name__ == "__main__":
    main()