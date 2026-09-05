import pandas as pd

METADATA_FILE = "india_sentinel1_metadata.csv"

# ------------------------------------------------------------
# FLOOD EVENT INPUT
# ------------------------------------------------------------

LAT = 16.3067
LON = 80.4365

FLOOD_DATE = "2024-08-25"

SEARCH_DAYS_BEFORE = 30
SEARCH_DAYS_AFTER = 30


# ------------------------------------------------------------
# Load metadata
# ------------------------------------------------------------

print("=" * 70)
print("INDIA SENTINEL-1 FLOOD PAIR SELECTOR")
print("=" * 70)

df = pd.read_csv(
    METADATA_FILE,
    low_memory=False
)

print("Total metadata scenes:", len(df))


# ------------------------------------------------------------
# Convert dates
# ------------------------------------------------------------

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce",
    utc=True
)

flood_date = pd.Timestamp(
    FLOOD_DATE,
    tz="UTC"
)

before_start = flood_date - pd.Timedelta(
    days=SEARCH_DAYS_BEFORE
)

after_end = flood_date + pd.Timedelta(
    days=SEARCH_DAYS_AFTER
)


# ------------------------------------------------------------
# Spatial filtering
# ------------------------------------------------------------

spatial = (
    (df["min_lon"] <= LON) &
    (df["max_lon"] >= LON) &
    (df["min_lat"] <= LAT) &
    (df["max_lat"] >= LAT)
)

df = df[spatial].copy()

print("Scenes covering location:", len(df))


# ------------------------------------------------------------
# Temporal filtering
# ------------------------------------------------------------

before = df[
    (df["date"] < flood_date) &
    (df["date"] >= before_start)
].copy()

after = df[
    (df["date"] >= flood_date) &
    (df["date"] <= after_end)
].copy()


# ------------------------------------------------------------
# Sort by distance from flood date
# ------------------------------------------------------------

before["distance_days"] = (
    flood_date - before["date"]
).dt.total_seconds() / 86400

after["distance_days"] = (
    after["date"] - flood_date
).dt.total_seconds() / 86400


before = before.sort_values(
    "distance_days"
)

after = after.sort_values(
    "distance_days"
)


# ------------------------------------------------------------
# Remove duplicate acquisition times
# ------------------------------------------------------------

before = before.drop_duplicates(
    subset=["date"],
    keep="first"
)

after = after.drop_duplicates(
    subset=["date"],
    keep="first"
)


# ------------------------------------------------------------
# Display candidates
# ------------------------------------------------------------

print()
print("=" * 70)
print("BEFORE-FLOOD CANDIDATES")
print("=" * 70)

if before.empty:

    print("No BEFORE scenes found.")

else:

    print(
        before[
            [
                "scene_id",
                "date",
                "distance_days",
                "orbit_state",
                "min_lon",
                "min_lat",
                "max_lon",
                "max_lat"
            ]
        ].head(10).to_string(index=False)
    )


print()
print("=" * 70)
print("AFTER-FLOOD CANDIDATES")
print("=" * 70)

if after.empty:

    print("No AFTER scenes found.")

else:

    print(
        after[
            [
                "scene_id",
                "date",
                "distance_days",
                "orbit_state",
                "min_lon",
                "min_lat",
                "max_lon",
                "max_lat"
            ]
        ].head(10).to_string(index=False)
    )


# ------------------------------------------------------------
# Select best pair
# ------------------------------------------------------------

print()
print("=" * 70)
print("SELECTED FLOOD PAIR")
print("=" * 70)

if before.empty or after.empty:

    print("Could not create a complete before/after pair.")

else:

    best_before = before.iloc[0]
    best_after = after.iloc[0]

    print()
    print("BEFORE SCENE")
    print("Scene :", best_before["scene_id"])
    print("Date  :", best_before["date"])
    print(
        "Days before flood:",
        round(best_before["distance_days"], 2)
    )

    print()
    print("AFTER SCENE")
    print("Scene :", best_after["scene_id"])
    print("Date  :", best_after["date"])
    print(
        "Days after flood:",
        round(best_after["distance_days"], 2)
    )

    # --------------------------------------------------------
    # Save pair
    # --------------------------------------------------------

    pair = pd.DataFrame([
        best_before,
        best_after
    ])

    pair["role"] = [
        "before",
        "after"
    ]

    pair.to_csv(
        "selected_flood_pair.csv",
        index=False
    )

    print()
    print("=" * 70)
    print("PAIR SELECTION COMPLETE")
    print("=" * 70)

    print(
        "Saved: selected_flood_pair.csv"
    )