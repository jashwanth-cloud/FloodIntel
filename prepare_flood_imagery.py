import pandas as pd
import requests
from pathlib import Path

STAC_URL = "https://stac.dataspace.copernicus.eu/v1"
PAIR_FILE = "selected_flood_pair.csv"
OUTPUT_FILE = "flood_imagery_assets.csv"

# ------------------------------------------------------------
# Load selected pair
# ------------------------------------------------------------

print("=" * 70)
print("FLOOD IMAGERY ASSET PREPARATION")
print("=" * 70)

df = pd.read_csv(
    PAIR_FILE,
    low_memory=False
)

print("Selected scenes:", len(df))

rows = []

# ------------------------------------------------------------
# Get STAC assets
# ------------------------------------------------------------

for _, row in df.iterrows():

    scene_id = row["scene_id"]

    print()
    print("-" * 70)
    print("Scene:", scene_id)

    url = (
        f"{STAC_URL}/collections/"
        f"sentinel-1-grd/items/{scene_id}"
    )

    response = requests.get(
        url,
        timeout=60
    )

    print("STAC HTTP:", response.status_code)

    response.raise_for_status()

    item = response.json()

    assets = item.get("assets", {})

    vv = assets.get("vv")
    vh = assets.get("vh")

    if not vv:
        print("WARNING: VV asset not found.")

    if not vh:
        print("WARNING: VH asset not found.")

    if vv:
        print("VV:", vv.get("href"))

    if vh:
        print("VH:", vh.get("href"))

    rows.append({
        "role": row["role"],
        "scene_id": scene_id,
        "date": row["date"],
        "orbit_state": row["orbit_state"],
        "vv_url": vv.get("href") if vv else "",
        "vh_url": vh.get("href") if vh else "",
    })


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_df = pd.DataFrame(rows)

output_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 70)
print("ASSET PREPARATION COMPLETE")
print("=" * 70)

print("Output:", OUTPUT_FILE)

print()
print(output_df.to_string(index=False))