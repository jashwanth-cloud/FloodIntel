import pandas as pd
import ast
from pathlib import Path


INPUT_FILE = Path("sentinel1_india_2018_2025_full.csv")
OUTPUT_FILE = Path("india_sentinel1_metadata.csv")


def parse_bbox(value):
    try:
        bbox = ast.literal_eval(value)

        if len(bbox) != 4:
            return [None, None, None, None]

        return bbox

    except Exception:
        return [None, None, None, None]


print("=" * 70)
print("INDIA SENTINEL-1 METADATA BUILDER")
print("=" * 70)

print("Reading:", INPUT_FILE)

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("Input scenes:", len(df))


# ------------------------------------------------------------
# Date
# ------------------------------------------------------------

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce",
    utc=True
)

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day


# ------------------------------------------------------------
# Bounding box
# ------------------------------------------------------------

print("Extracting bounding boxes...")

bbox_values = df["bbox"].apply(parse_bbox)

bbox_df = pd.DataFrame(
    bbox_values.tolist(),
    columns=[
        "min_lon",
        "min_lat",
        "max_lon",
        "max_lat"
    ]
)

df = pd.concat(
    [df, bbox_df],
    axis=1
)


# ------------------------------------------------------------
# Scene center
# ------------------------------------------------------------

df["center_lon"] = (
    df["min_lon"] +
    df["max_lon"]
) / 2

df["center_lat"] = (
    df["min_lat"] +
    df["max_lat"]
) / 2


# ------------------------------------------------------------
# Clean polarization
# ------------------------------------------------------------

df["polarizations"] = (
    df["polarizations"]
    .astype(str)
    .str.replace(" ", "", regex=False)
)


# ------------------------------------------------------------
# Keep useful columns
# ------------------------------------------------------------

columns = [
    "scene_id",
    "date",
    "year",
    "month",
    "day",
    "platform",
    "product_type",
    "instrument_mode",
    "polarizations",
    "orbit",
    "orbit_state",
    "min_lon",
    "min_lat",
    "max_lon",
    "max_lat",
    "center_lon",
    "center_lat",
]

df = df[columns]


# ------------------------------------------------------------
# Remove duplicates
# ------------------------------------------------------------

before = len(df)

df = df.drop_duplicates(
    subset=["scene_id"]
)

after = len(df)

print(
    f"Removed duplicates: {before - after}"
)


# ------------------------------------------------------------
# Sort
# ------------------------------------------------------------

df = df.sort_values(
    "date"
).reset_index(drop=True)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print()
print("=" * 70)
print("METADATA BUILD COMPLETE")
print("=" * 70)

print("Final scenes:", len(df))
print("Output:", OUTPUT_FILE)

print()
print("Date range:")

print(
    df["date"].min(),
    "→",
    df["date"].max()
)

print()
print("Platforms:")

print(
    df["platform"].value_counts()
)

print()
print("Instrument modes:")

print(
    df["instrument_mode"].value_counts()
)

print()
print("Polarizations:")

print(
    df["polarizations"].value_counts()
)

print()
print("Missing bounding boxes:")

print(
    df[
        [
            "min_lon",
            "min_lat",
            "max_lon",
            "max_lat"
        ]
    ]
    .isna()
    .any(axis=1)
    .sum()
)

print()
print("=" * 70)