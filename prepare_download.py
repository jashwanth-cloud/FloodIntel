import pandas as pd

INPUT_FILE = "selected_flood_scenes.csv"
OUTPUT_FILE = "download_queue.csv"

TARGET_PER_YEAR = 75

print("=" * 70)
print("PREPARING SENTINEL-1 FLOOD DOWNLOAD QUEUE")
print("=" * 70)

df = pd.read_csv(INPUT_FILE, low_memory=False)

df["date"] = pd.to_datetime(df["date"], errors="coerce")

df = df.dropna(subset=["scene_id", "date", "center_lat", "center_lon"])

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

print(f"Available scenes: {len(df)}")

selected = []

for year in sorted(df["year"].unique()):

    year_df = df[df["year"] == year].copy()

    print(f"\nYear {year}: {len(year_df)} available")

    # Prefer known orbit states
    known = year_df[year_df["orbit_state"].isin(["ascending", "descending"])]

    if len(known) >= TARGET_PER_YEAR:
        year_df = known

    # Reproducible random selection
    sample_size = min(TARGET_PER_YEAR, len(year_df))

    sample = year_df.sample(
        n=sample_size,
        random_state=42
    )

    selected.append(sample)

    print(f"Selected: {len(sample)}")

result = pd.concat(selected, ignore_index=True)

# Sort chronologically
result = result.sort_values("date")

# Remove accidental duplicates
result = result.drop_duplicates(subset=["scene_id"])

# Save only useful download information
columns = [
    "scene_id",
    "date",
    "platform",
    "product_type",
    "instrument_mode",
    "polarizations",
    "orbit_state",
    "bbox",
    "center_lat",
    "center_lon"
]

result[columns].to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 70)
print("DOWNLOAD QUEUE READY")
print("=" * 70)
print(f"Selected scenes: {len(result)}")
print(f"Output: {OUTPUT_FILE}")

print()
print("Scenes by year:")
print(result["date"].dt.year.value_counts().sort_index())

print()
print("Scenes by month:")
print(result["date"].dt.month.value_counts().sort_index())

print()
print("Orbit:")
print(result["orbit_state"].value_counts(dropna=False))

print()
print("=" * 70)