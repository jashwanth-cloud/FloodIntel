import pandas as pd
from pathlib import Path

INPUT_FILE = Path("india_sentinel1_metadata.csv")

print("=" * 70)
print("INDIA SENTINEL-1 METADATA SUMMARY")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"Total scenes: {len(df):,}")
print()

# ------------------------------------------------------------
# DATE
# ------------------------------------------------------------

df["date"] = pd.to_datetime(df["date"], errors="coerce")

print("=" * 70)
print("DATE RANGE")
print("=" * 70)

print("First scene:", df["date"].min())
print("Last scene :", df["date"].max())
print()

# ------------------------------------------------------------
# YEAR
# ------------------------------------------------------------

print("=" * 70)
print("SCENES PER YEAR")
print("=" * 70)

year_counts = df.groupby("year").size()

print(year_counts.to_string())
print()

# ------------------------------------------------------------
# MONTH
# ------------------------------------------------------------

print("=" * 70)
print("SCENES PER MONTH")
print("=" * 70)

month_counts = df.groupby("month").size()

print(month_counts.to_string())
print()

# ------------------------------------------------------------
# PLATFORM
# ------------------------------------------------------------

print("=" * 70)
print("PLATFORMS")
print("=" * 70)

print(df["platform"].value_counts(dropna=False).to_string())
print()

# ------------------------------------------------------------
# INSTRUMENT MODE
# ------------------------------------------------------------

print("=" * 70)
print("INSTRUMENT MODES")
print("=" * 70)

print(df["instrument_mode"].value_counts(dropna=False).to_string())
print()

# ------------------------------------------------------------
# POLARIZATION
# ------------------------------------------------------------

print("=" * 70)
print("POLARIZATIONS")
print("=" * 70)

print(df["polarizations"].value_counts(dropna=False).to_string())
print()

# ------------------------------------------------------------
# ORBIT STATE
# ------------------------------------------------------------

print("=" * 70)
print("ORBIT STATES")
print("=" * 70)

print(df["orbit_state"].value_counts(dropna=False).to_string())
print()

# ------------------------------------------------------------
# PRODUCT TYPE
# ------------------------------------------------------------

print("=" * 70)
print("PRODUCT TYPES")
print("=" * 70)

print(df["product_type"].value_counts(dropna=False).to_string())
print()

# ------------------------------------------------------------
# GEOGRAPHIC EXTENT
# ------------------------------------------------------------

print("=" * 70)
print("INDIA DATASET GEOGRAPHIC EXTENT")
print("=" * 70)

print("Minimum longitude:", df["min_lon"].min())
print("Maximum longitude:", df["max_lon"].max())
print("Minimum latitude :", df["min_lat"].min())
print("Maximum latitude :", df["max_lat"].max())
print()

# ------------------------------------------------------------
# CENTER COVERAGE
# ------------------------------------------------------------

print("=" * 70)
print("CENTER COORDINATE RANGE")
print("=" * 70)

print("Center longitude:", df["center_lon"].min(), "→", df["center_lon"].max())
print("Center latitude :", df["center_lat"].min(), "→", df["center_lat"].max())
print()

# ------------------------------------------------------------
# MISSING VALUES
# ------------------------------------------------------------

print("=" * 70)
print("MISSING VALUES")
print("=" * 70)

missing = df.isna().sum()

print(missing[missing > 0].to_string())
print()

# ------------------------------------------------------------
# SAVE SUMMARY
# ------------------------------------------------------------

summary = {
    "total_scenes": len(df),
    "first_date": str(df["date"].min()),
    "last_date": str(df["date"].max()),
    "min_longitude": df["min_lon"].min(),
    "max_longitude": df["max_lon"].max(),
    "min_latitude": df["min_lat"].min(),
    "max_latitude": df["max_lat"].max(),
}

summary_df = pd.DataFrame([summary])

summary_df.to_csv("india_metadata_summary.csv", index=False)

print("=" * 70)
print("SUMMARY COMPLETE")
print("=" * 70)
print("Saved: india_metadata_summary.csv")