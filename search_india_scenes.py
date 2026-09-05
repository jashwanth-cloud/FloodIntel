import pandas as pd
from pathlib import Path

INPUT_FILE = Path("india_sentinel1_metadata.csv")

print("=" * 70)
print("INDIA SENTINEL-1 SCENE SEARCH")
print("=" * 70)

lat = float(input("Enter latitude : "))
lon = float(input("Enter longitude: "))

start_date = input("Start date (YYYY-MM-DD): ")
end_date = input("End date   (YYYY-MM-DD): ")

df = pd.read_csv(INPUT_FILE, low_memory=False)

df["date"] = pd.to_datetime(df["date"], errors="coerce")

start = pd.Timestamp(start_date, tz="UTC")
end = pd.Timestamp(end_date, tz="UTC")

# ------------------------------------------------------------
# Geographic coverage test
# ------------------------------------------------------------

covers_location = (
    (df["min_lon"] <= lon) &
    (df["max_lon"] >= lon) &
    (df["min_lat"] <= lat) &
    (df["max_lat"] >= lat)
)

# ------------------------------------------------------------
# Date filter
# ------------------------------------------------------------

date_match = (
    (df["date"] >= start) &
    (df["date"] <= end)
)

result = df[covers_location & date_match].copy()

result = result.sort_values("date")

print()
print("=" * 70)
print("SEARCH RESULT")
print("=" * 70)

print("Location:")
print("Latitude :", lat)
print("Longitude:", lon)

print()
print("Date range:")
print(start_date, "→", end_date)

print()
print("Scenes found:", len(result))

if len(result) > 0:
    columns = [
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

    print()
    print(result[columns].to_string(index=False))

    result.to_csv("location_scene_search.csv", index=False)

    print()
    print("Saved: location_scene_search.csv")

else:
    print()
    print("No Sentinel-1 scenes found for this location/date range.")