import pandas as pd
from pathlib import Path

INPUT_FILE = Path("flood_event_search.csv")
OUTPUT_FILE = Path("flood_event_analysis.csv")

print("=" * 70)
print("FLOOD EVENT METADATA ANALYZER")
print("=" * 70)

df = pd.read_csv(INPUT_FILE, low_memory=False)

if df.empty:
    print("No flood event data found.")
    raise SystemExit(1)

df["date"] = pd.to_datetime(df["date"], utc=True)

before = df[df["role"] == "before"]

after = df[df["role"] == "after"]

if before.empty or after.empty:
    print("A complete before/after pair is required.")
    raise SystemExit(1)

before = before.iloc[0]
after = after.iloc[0]

# ------------------------------------------------------------
# Temporal analysis
# ------------------------------------------------------------

before_date = before["date"]
after_date = after["date"]

time_gap = (
    after_date - before_date
).total_seconds() / 86400

# ------------------------------------------------------------
# Spatial consistency
# ------------------------------------------------------------

same_bbox = (
    abs(before["min_lon"] - after["min_lon"]) < 0.1
    and abs(before["max_lon"] - after["max_lon"]) < 0.1
    and abs(before["min_lat"] - after["min_lat"]) < 0.1
    and abs(before["max_lat"] - after["max_lat"]) < 0.1
)

# ------------------------------------------------------------
# Orbit consistency
# ------------------------------------------------------------

same_orbit_state = (
    str(before["orbit_state"])
    == str(after["orbit_state"])
)

# ------------------------------------------------------------
# Polarization
# ------------------------------------------------------------

polarization = str(before["polarizations"])

has_vv = "VV" in polarization
has_vh = "VH" in polarization

# ------------------------------------------------------------
# Suitability score
# ------------------------------------------------------------

score = 0
reasons = []

if time_gap <= 30:
    score += 30
    reasons.append("Temporal gap is within 30 days.")

if same_bbox:
    score += 25
    reasons.append("Before/after scenes have consistent coverage.")

if same_orbit_state:
    score += 20
    reasons.append("Before/after scenes use the same orbit direction.")

if has_vv and has_vh:
    score += 25
    reasons.append("Both VV and VH polarizations are available.")

# ------------------------------------------------------------
# Classification
# ------------------------------------------------------------

if score >= 80:
    assessment = "HIGHLY SUITABLE"
elif score >= 60:
    assessment = "SUITABLE"
elif score >= 40:
    assessment = "PARTIALLY SUITABLE"
else:
    assessment = "LOW SUITABILITY"

# ------------------------------------------------------------
# Display
# ------------------------------------------------------------

print()
print("=" * 70)
print("FLOOD EVENT ANALYSIS")
print("=" * 70)

print()
print("BEFORE SCENE")
print("-" * 70)
print("Scene :", before["scene_id"])
print("Date  :", before_date)
print("Orbit :", before["orbit_state"])

print()
print("AFTER SCENE")
print("-" * 70)
print("Scene :", after["scene_id"])
print("Date  :", after_date)
print("Orbit :", after["orbit_state"])

print()
print("=" * 70)
print("ANALYSIS")
print("=" * 70)

print(f"Temporal gap       : {time_gap:.2f} days")
print(f"Same coverage     : {'YES' if same_bbox else 'NO'}")
print(f"Same orbit state  : {'YES' if same_orbit_state else 'NO'}")
print(f"VV available      : {'YES' if has_vv else 'NO'}")
print(f"VH available      : {'YES' if has_vh else 'NO'}")

print()
print(f"SUITABILITY SCORE  : {score}/100")
print(f"ASSESSMENT         : {assessment}")

print()
print("REASONS")
print("-" * 70)

for reason in reasons:
    print("✓", reason)

# ------------------------------------------------------------
# Save report
# ------------------------------------------------------------

result = pd.DataFrame([{
    "before_scene": before["scene_id"],
    "before_date": before_date,
    "after_scene": after["scene_id"],
    "after_date": after_date,
    "temporal_gap_days": round(time_gap, 2),
    "same_coverage": same_bbox,
    "same_orbit_state": same_orbit_state,
    "vv_available": has_vv,
    "vh_available": has_vh,
    "suitability_score": score,
    "assessment": assessment
}])

result.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"Saved: {OUTPUT_FILE}")