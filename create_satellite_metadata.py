import pandas as pd
import rasterio
from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# SATELLITE METADATA GENERATOR
# ============================================================

AOI_DIR = Path("flood_aoi")
OUTPUT_DIR = Path("metadata")

OUTPUT_DIR.mkdir(exist_ok=True)

BEFORE_FILE = AOI_DIR / "before_vv_vh.tiff"
AFTER_FILE = AOI_DIR / "after_vv_vh.tiff"

records = []

scenes = [
    {
        "role": "before",
        "scene_id": "S1A_IW_GRDH_1SDV_20240820T003107_20240820T003132_055289_06BD9B_5392_COG",
        "acquisition_date": "2024-08-20",
        "orbit_direction": "descending",
        "satellite": "Sentinel-1A",
        "polarizations": "VV,VH",
        "file": BEFORE_FILE,
    },
    {
        "role": "after",
        "scene_id": "S1A_IW_GRDH_1SDV_20240901T003107_20240901T003132_055464_06C415_8969_COG",
        "acquisition_date": "2024-09-01",
        "orbit_direction": "descending",
        "satellite": "Sentinel-1A",
        "polarizations": "VV,VH",
        "file": AFTER_FILE,
    },
]

print("=" * 70)
print("SATELLITE METADATA GENERATOR")
print("=" * 70)

for scene in scenes:

    file = scene["file"]

    print()
    print("-" * 70)
    print("Processing:", scene["role"].upper())
    print("File:", file)

    if not file.exists():
        print("ERROR: File not found.")
        continue

    with rasterio.open(file) as src:

        bounds = src.bounds

        record = {
            "role": scene["role"],
            "scene_id": scene["scene_id"],
            "satellite": scene["satellite"],
            "acquisition_date": scene["acquisition_date"],
            "orbit_direction": scene["orbit_direction"],
            "polarizations": scene["polarizations"],

            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,

            "resolution_x": src.res[0],
            "resolution_y": src.res[1],

            "west": bounds.left,
            "south": bounds.bottom,
            "east": bounds.right,
            "north": bounds.top,

            "bands": src.count,
            "data_type": ",".join(src.dtypes),

            "source": "Copernicus Data Space Ecosystem",
            "processing_api": "CDSE Sentinel Hub Process API",
        }

        records.append(record)

        print("CRS:", src.crs)
        print("Size:", src.width, "x", src.height)
        print("Bands:", src.count)
        print("Bounds:", bounds)

# ------------------------------------------------------------
# Save metadata
# ------------------------------------------------------------

output_file = OUTPUT_DIR / "satellite_metadata.csv"

df = pd.DataFrame(records)

df.to_csv(output_file, index=False)

print()
print("=" * 70)
print("METADATA GENERATION COMPLETE")
print("=" * 70)

print()
print("Records:", len(df))
print("Saved:", output_file)

print()
print(df.to_string(index=False))