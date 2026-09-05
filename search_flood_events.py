import pandas as pd
from pathlib import Path

INPUT_FILE = Path("india_sentinel1_metadata.csv")
OUTPUT_FILE = Path("flood_event_search.csv")


def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def get_date(prompt):
    while True:
        try:
            return pd.Timestamp(input(prompt), tz="UTC")
        except Exception:
            print("Please enter the date as YYYY-MM-DD.")


print("=" * 70)
print("INDIA-WIDE SENTINEL-1 FLOOD EVENT SEARCH")
print("=" * 70)

# ------------------------------------------------------------
# Load metadata
# ------------------------------------------------------------

print(f"Reading: {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE, low_memory=False)

df["date"] = pd.to_datetime(df["date"], utc=True)

print(f"Total metadata scenes: {len(df):,}")

# ------------------------------------------------------------
# User input
# ------------------------------------------------------------

print()
print("-" * 70)

latitude = get_float("Enter latitude : ")
longitude = get_float("Enter longitude: ")

event_date = get_date("Flood/event date (YYYY-MM-DD): ")

window_days = int(
    input("Search window around event (days, e.g. 30): ")
)

print()
print("=" * 70)
print("SEARCHING INDIA-WIDE SENTINEL-1 METADATA")
print("=" * 70)

print(f"Latitude : {latitude}")
print(f"Longitude: {longitude}")
print(f"Event    : {event_date.date()}")
print(f"Window   : ±{window_days} days")

# ------------------------------------------------------------
# Check spatial coverage
# ------------------------------------------------------------

covers_location = (
    (df["min_lon"] <= longitude)
    & (df["max_lon"] >= longitude)
    & (df["min_lat"] <= latitude)
    & (df["max_lat"] >= latitude)
)

spatial = df[covers_location].copy()

print()
print(f"Scenes covering location: {len(spatial)}")

if spatial.empty:
    print()
    print("NO SENTINEL-1 SCENES COVER THIS LOCATION.")
    raise SystemExit(0)

# ------------------------------------------------------------
# Restrict date range
# ------------------------------------------------------------

start_date = event_date - pd.Timedelta(days=window_days)
end_date = event_date + pd.Timedelta(days=window_days)

candidates = spatial[
    (spatial["date"] >= start_date)
    & (spatial["date"] <= end_date)
].copy()

print(
    f"Scenes inside date window: {len(candidates)}"
)

if candidates.empty:
    print()
    print("NO SCENES FOUND IN THE DATE WINDOW.")
    raise SystemExit(0)

# ------------------------------------------------------------
# Calculate distance from event date
# ------------------------------------------------------------

candidates["distance_days"] = (
    candidates["date"] - event_date
).abs().dt.total_seconds() / 86400

# ------------------------------------------------------------
# BEFORE scenes
# ------------------------------------------------------------

before = candidates[
    candidates["date"] < event_date
].copy()

before = before.sort_values(
    "distance_days"
)

# ------------------------------------------------------------
# AFTER scenes
# ------------------------------------------------------------

after = candidates[
    candidates["date"] > event_date
].copy()

after = after.sort_values(
    "distance_days"
)

# ------------------------------------------------------------
# Display candidates
# ------------------------------------------------------------

print()
print("=" * 70)
print("BEFORE-EVENT CANDIDATES")
print("=" * 70)

if before.empty:
    print("No before-event scenes found.")
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
                "max_lat",
            ]
        ].head(10).to_string(index=False)
    )

print()
print("=" * 70)
print("AFTER-EVENT CANDIDATES")
print("=" * 70)

if after.empty:
    print("No after-event scenes found.")
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
                "max_lat",
            ]
        ].head(10).to_string(index=False)
    )

# ------------------------------------------------------------
# Select closest pair
# ------------------------------------------------------------

selected = []

if not before.empty:
    row = before.iloc[0].copy()
    row["role"] = "before"
    selected.append(row)

if not after.empty:
    row = after.iloc[0].copy()
    row["role"] = "after"
    selected.append(row)

print()
print("=" * 70)
print("SELECTED FLOOD EVENT PAIR")
print("=" * 70)

if len(selected) < 2:

    print()
    print("Could not find both a BEFORE and AFTER scene.")
    print("Try increasing the search window.")

else:

    result = pd.DataFrame(selected)

    for _, row in result.iterrows():

        print()
        print(row["role"].upper())

        print("Scene :", row["scene_id"])
        print("Date  :", row["date"])
        print(
            "Distance from event:",
            round(row["distance_days"], 2),
            "days"
        )

        print(
            "Orbit:",
            row["orbit_state"]
        )

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("FLOOD EVENT SEARCH COMPLETE")
    print("=" * 70)

    print(f"Saved: {OUTPUT_FILE}")

    print()
    print("This pair can now be used by the next stage")
    print("of the flood-analysis pipeline.")