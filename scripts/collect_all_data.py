from pathlib import Path
import json
from datetime import datetime


# ============================================================
# SIH 26071 — MASTER DATA COLLECTOR
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def check_file(path: Path, name: str):
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)

        print(f"  ✓ {name}")
        print(f"      {path}")
        print(f"      Size: {size_mb:.2f} MB")

        return True

    print(f"  ✗ {name} — NOT FOUND")
    print(f"      Expected: {path}")

    return False


def check_directory(path: Path, name: str):
    if path.exists():
        files = list(path.rglob("*"))

        print(f"  ✓ {name}")
        print(f"      {path}")
        print(f"      Items: {len(files)}")

        return True

    print(f"  ✗ {name} — NOT FOUND")
    print(f"      Expected: {path}")

    return False


def main():

    print()
    print("=" * 72)
    print("SIH 26071 — INDIA FLOOD DATA MASTER COLLECTOR")
    print("=" * 72)

    print(f"\nProject root:")
    print(f"  {PROJECT_ROOT}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "datasets": {}
    }

    # --------------------------------------------------------
    # 1. IMD RAINFALL
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[1] IMD GRIDDed RAINFALL")
    print("-" * 72)

    rainfall_dir = DATA_RAW / "rainfall"

    rainfall_ok = check_directory(
        rainfall_dir,
        "Rainfall directory"
    )

    report["datasets"]["rainfall"] = {
        "status": "present" if rainfall_ok else "missing",
        "path": str(rainfall_dir)
    }

    # --------------------------------------------------------
    # 2. SURFACE WATERBODIES
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[2] SURFACE WATERBODIES")
    print("-" * 72)

    waterbody_file = (
        DATA_RAW
        / "hydrology"
        / "water_bodies"
        / "india"
        / "india_surface_waterbodies.geojson"
    )

    waterbody_ok = check_file(
        waterbody_file,
        "India-wide surface waterbodies"
    )

    report["datasets"]["surface_waterbodies"] = {
        "status": "present" if waterbody_ok else "missing",
        "path": str(waterbody_file)
    }

    # --------------------------------------------------------
    # 3. HYDROLOGY DIRECTORY
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[3] HYDROLOGY")
    print("-" * 72)

    hydrology_dir = DATA_RAW / "hydrology"

    hydrology_ok = check_directory(
        hydrology_dir,
        "Hydrology data"
    )

    report["datasets"]["hydrology"] = {
        "status": "present" if hydrology_ok else "missing",
        "path": str(hydrology_dir)
    }

    # --------------------------------------------------------
    # 4. SENTINEL-1
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[4] SENTINEL-1")
    print("-" * 72)

    sentinel_dir = DATA_RAW / "sentinel1"

    sentinel_ok = check_directory(
        sentinel_dir,
        "Sentinel-1 data"
    )

    report["datasets"]["sentinel1"] = {
        "status": "present" if sentinel_ok else "missing",
        "path": str(sentinel_dir)
    }

    # --------------------------------------------------------
    # 5. DEM
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[5] DEM / ELEVATION")
    print("-" * 72)

    dem_dir = DATA_RAW / "dem"

    dem_ok = check_directory(
        dem_dir,
        "DEM data"
    )

    report["datasets"]["dem"] = {
        "status": "present" if dem_ok else "missing",
        "path": str(dem_dir)
    }

    # --------------------------------------------------------
    # 6. SOIL
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[6] SOIL")
    print("-" * 72)

    soil_dir = DATA_RAW / "soil"

    soil_ok = check_directory(
        soil_dir,
        "Soil data"
    )

    report["datasets"]["soil"] = {
        "status": "present" if soil_ok else "missing",
        "path": str(soil_dir)
    }

    # --------------------------------------------------------
    # SAVE REPORT
    # --------------------------------------------------------

    report_file = REPORT_DIR / "data_collection_report.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 72)
    print("DATA COLLECTION CHECK COMPLETE")
    print("=" * 72)

    print(f"\nReport:")
    print(f"  {report_file}")

    print("\nNext step:")
    print("  Missing datasets will be connected to their")
    print("  official download sources in the next version.")


if __name__ == "__main__":
    main()