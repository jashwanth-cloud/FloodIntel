import pandas as pd

METADATA_FILE = "india_sentinel1_metadata.csv"

# ------------------------------------------------------------
# Example target location
# ------------------------------------------------------------

LAT = 16.3067
LON = 80.4365

# Search window
START_DATE = "2024-08-01"
END_DATE = "2024-09-15"

# ------------------------------------------------------------
# Load metadata
# ------------------------------------------------------------

print("=" * 70)
print("INDIA SENTINEL-1 FLOOD SCENE SELECTOR")
print("=" * 70)

df = pd.read_csv(
    METADATA_FILE,
    low_memory=False
)

print("Total scenes:", len(df))

# ------------------------------------------------------------
# Convert dates
# ------------------------------------------------------------

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce",
    utc=True
)

start = pd.Timestamp(
    START_DATE,
    tz="UTC"
)

end = pd.Timestamp(
    END_DATE,
    tz="UTC"
)

# ------------------------------------------------------------
# Spatial filter
#
# Target point must be inside scene BBOX
# ------------------------------------------------------------

spatial = (
    (df["min_lon"] <= LON) &
    (df["max_lon"] >= LON) &
    (df["min_lat"] <= LAT) &
    (df["max_lat"] >= LAT)
)

temporal = (
    (df["date"] >= start) &
    (df["date"] < end)
)

matches = df[
    spatial & temporal
].copy()

# ------------------------------------------------------------
# Sort by acquisition time
# ------------------------------------------------------------

matches = matches.sort_values(
    "date"
)

print()
print("Target:")
print("Latitude :", LAT)
print("Longitude:", LON)

print()
print("Date range:")
print(START_DATE, "→", END_DATE)

print()
print("=" * 70)
print("MATCHING SENTINEL-1 SCENES")
print("=" * 70)

print("Scenes found:", len(matches))

if len(matches) == 0:

    print()
    print("No Sentinel-1 scenes found.")

else:

    print()

    print(
        matches[
            [
                "scene_id",
                "date",
                "platform",
                "polarizations",
                "orbit_state",
                "min_lon",
                "min_lat",
                "max_lon",
                "max_lat"
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    output = "selected_flood_scenes.csv"

    matches.to_csv(
        output,
        index=False
    )

    print()
    print("=" * 70)
    print("SELECTION COMPLETE")
    print("=" * 70)

    print("Saved:", output)