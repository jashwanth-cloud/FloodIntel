"""
Phase 3 — Step 7: Data Quality Control
=======================================
Automated validation checks for the assembled feature dataset.
Generates docs/PHASE3_DATA_QUALITY.md with statistics and anomalies.
"""

import os
import sys
import json
import logging
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("quality_control")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

AOI_BOUNDS = {
    "lat_min": 16.2567,
    "lat_max": 16.3567,
    "lon_min": 80.3865,
    "lon_max": 80.4865,
}


def check_duplicates(df):
    """Check for duplicate records."""
    dups = df.duplicated(subset=["lat", "lon", "date"]).sum()
    return {"duplicate_rows": int(dups), "status": "PASS" if dups == 0 else "WARN"}


def check_missing_values(df):
    """Compute missing value statistics per column."""
    results = {}
    for col in df.columns:
        n_missing = int(df[col].isnull().sum())
        pct_missing = round(100.0 * n_missing / len(df), 3)
        results[col] = {"n_missing": n_missing, "pct_missing": pct_missing}
    return results


def check_rainfall_values(df):
    """Check for impossible rainfall values."""
    issues = []
    rain_cols = [c for c in df.columns if "rainfall" in c]
    for col in rain_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        n_negative = int((s < 0).sum())
        n_extreme = int((s > 600).sum())  # >600mm/day is physically extreme
        if n_negative > 0:
            issues.append(f"{col}: {n_negative} negative values (INVALID)")
        if n_extreme > 0:
            issues.append(f"{col}: {n_extreme} values >600mm/day (EXTREME — verify)")
    return {"issues": issues, "status": "PASS" if not issues else "WARN"}


def check_coordinates(df):
    """Check for invalid lat/lon values."""
    issues = []
    if "lat" in df.columns:
        out_of_range = int(((df["lat"] < -90) | (df["lat"] > 90)).sum())
        out_of_aoi = int(
            ((df["lat"] < AOI_BOUNDS["lat_min"] - 0.01) |
             (df["lat"] > AOI_BOUNDS["lat_max"] + 0.01)).sum()
        )
        if out_of_range > 0:
            issues.append(f"lat: {out_of_range} values outside [-90, 90]")
        if out_of_aoi > 0:
            issues.append(f"lat: {out_of_aoi} values outside AOI bounds (minor overflow ok)")
    if "lon" in df.columns:
        out_of_range = int(((df["lon"] < -180) | (df["lon"] > 180)).sum())
        if out_of_range > 0:
            issues.append(f"lon: {out_of_range} values outside [-180, 180]")
    return {"issues": issues, "status": "PASS" if not issues else "WARN"}


def check_sentinel1_features(df):
    """Check Sentinel-1 features for impossible values."""
    issues = []
    s1_cols = [c for c in df.columns if c in [
        "before_vv", "before_vh", "after_vv", "after_vh",
        "vv_change", "vh_change", "vv_ratio", "vh_ratio",
        "before_vv_vh_ratio", "after_vv_vh_ratio", "vv_vh_change"
    ]]
    for col in s1_cols:
        s = df[col].dropna()
        if len(s) == 0:
            issues.append(f"{col}: ALL values missing")
            continue
        # SAR backscatter (linear scale after normalization): should be finite
        n_inf = int(np.isinf(s).sum())
        n_nan_after_drop = int(s.isnull().sum())
        if n_inf > 0:
            issues.append(f"{col}: {n_inf} infinite values")
    return {"issues": issues, "s1_cols_checked": len(s1_cols), "status": "PASS" if not issues else "WARN"}


def check_temporal_consistency(df):
    """Check for temporal consistency."""
    issues = []
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"]).dropna()
        unique_dates = dates.unique()
        if len(unique_dates) == 0:
            issues.append("No valid dates found")
        # For the AOI dataset, we expect exactly one date
        if len(unique_dates) > 1:
            issues.append(f"Multiple dates found: {sorted(unique_dates)[:5]} (expected 1 for AOI)")
    return {
        "unique_dates": [str(d)[:10] for d in sorted(unique_dates)] if "date" in df.columns else [],
        "issues": issues,
        "status": "PASS" if not issues else "INFO"
    }


def check_flood_label_distribution(df):
    """Check flood label distribution."""
    if "flood_label" not in df.columns:
        return {"status": "SKIP", "reason": "flood_label column not found"}
    labels = df["flood_label"].dropna()
    vc = labels.value_counts().to_dict()
    n_total = len(labels)
    flood_pct = round(100.0 * vc.get(1, 0) / max(n_total, 1), 3)
    return {
        "class_distribution": {str(k): int(v) for k, v in vc.items()},
        "flood_percentage": flood_pct,
        "class_imbalance_ratio": round(vc.get(0, 0) / max(vc.get(1, 1), 1), 1),
        "status": "INFO"
    }


def compute_feature_statistics(df):
    """Compute basic statistics for all numeric columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats = {}
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) == 0:
            stats[col] = {"count": 0, "status": "ALL_NULL"}
            continue
        stats[col] = {
            "count": int(len(s)),
            "mean": round(float(s.mean()), 6),
            "std": round(float(s.std()), 6),
            "min": round(float(s.min()), 6),
            "p25": round(float(s.quantile(0.25)), 6),
            "median": round(float(s.median()), 6),
            "p75": round(float(s.quantile(0.75)), 6),
            "max": round(float(s.max()), 6),
            "n_outliers_3sigma": int(((s - s.mean()).abs() > 3 * s.std()).sum()),
        }
    return stats


def run_quality_control():
    """Run all QC checks and generate the quality report."""
    log.info("=" * 60)
    log.info("PHASE 3 — Data Quality Control")
    log.info("=" * 60)

    report = {
        "generated_at": datetime.now().isoformat(),
        "checks": {},
        "feature_statistics": {},
        "datasets_checked": [],
    }

    # ── Check 1: Main feature dataset ─────────────────────────────────────────
    feature_path = os.path.join(FEATURES_DIR, "flood_features.parquet")
    if os.path.exists(feature_path):
        log.info(f"Loading feature dataset: {feature_path}")
        df = pd.read_parquet(feature_path)
        log.info(f"  Shape: {df.shape}")

        report["datasets_checked"].append({
            "name": "flood_features.parquet",
            "path": feature_path,
            "size_mb": round(os.path.getsize(feature_path) / 1e6, 3),
            "shape": list(df.shape),
            "columns": list(df.columns),
            "date_range": {
                "min": str(df["date"].min()) if "date" in df.columns else "N/A",
                "max": str(df["date"].max()) if "date" in df.columns else "N/A",
            },
            "spatial_extent": {
                "lat_min": float(df["lat"].min()) if "lat" in df.columns else None,
                "lat_max": float(df["lat"].max()) if "lat" in df.columns else None,
                "lon_min": float(df["lon"].min()) if "lon" in df.columns else None,
                "lon_max": float(df["lon"].max()) if "lon" in df.columns else None,
            }
        })

        # Run checks
        report["checks"]["duplicates"] = check_duplicates(df)
        report["checks"]["missing_values"] = check_missing_values(df)
        report["checks"]["rainfall_validation"] = check_rainfall_values(df)
        report["checks"]["coordinate_validation"] = check_coordinates(df)
        report["checks"]["sentinel1_validation"] = check_sentinel1_features(df)
        report["checks"]["temporal_consistency"] = check_temporal_consistency(df)
        report["checks"]["flood_label_distribution"] = check_flood_label_distribution(df)
        report["feature_statistics"]["flood_features"] = compute_feature_statistics(df)

        log.info("\nQC Results:")
        for check_name, result in report["checks"].items():
            status = result.get("status", "?")
            log.info(f"  {check_name}: {status}")
            if "issues" in result and result["issues"]:
                for issue in result["issues"]:
                    log.warning(f"    ⚠ {issue}")
    else:
        log.warning(f"Feature dataset not found: {feature_path}")
        report["checks"]["feature_dataset"] = {"status": "MISSING", "path": feature_path}

    # ── Check 2: Rainfall daily ───────────────────────────────────────────────
    rain_path = os.path.join(FEATURES_DIR, "rainfall_daily.parquet")
    if os.path.exists(rain_path):
        rain_df = pd.read_parquet(rain_path)
        rain_df["date"] = pd.to_datetime(rain_df["date"])
        report["datasets_checked"].append({
            "name": "rainfall_daily.parquet",
            "shape": list(rain_df.shape),
            "date_range": {
                "min": str(rain_df["date"].min()),
                "max": str(rain_df["date"].max()),
            },
            "grid_cells": int(rain_df[["lat", "lon"]].drop_duplicates().shape[0]),
            "rainfall_stats": {
                "min_mm": float(rain_df["rainfall_mm"].min()),
                "max_mm": float(rain_df["rainfall_mm"].max()),
                "mean_mm": float(rain_df["rainfall_mm"].mean()),
                "n_negative": int((rain_df["rainfall_mm"] < 0).sum()),
            }
        })

    # ── Check 3: Hydrology features ───────────────────────────────────────────
    hydro_path = os.path.join(FEATURES_DIR, "hydrology_features_aoi.parquet")
    if os.path.exists(hydro_path):
        h_df = pd.read_parquet(hydro_path)
        report["datasets_checked"].append({
            "name": "hydrology_features_aoi.parquet",
            "shape": list(h_df.shape),
            "columns": list(h_df.columns),
        })

    # ── Write JSON report ─────────────────────────────────────────────────────
    json_out = os.path.join(DOCS_DIR, "phase3_qc_report.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    log.info(f"\nQC JSON report saved: {json_out}")

    # ── Write Markdown report ─────────────────────────────────────────────────
    write_markdown_report(report)

    return report


def write_markdown_report(report):
    """Write a human-readable Markdown QC report."""
    md_path = os.path.join(DOCS_DIR, "PHASE3_DATA_QUALITY.md")

    lines = [
        "# Phase 3 — Data Quality Report",
        f"\nGenerated: {report.get('generated_at', 'N/A')}",
        "\n---",
        "\n## Datasets Checked",
        "",
    ]

    for ds in report.get("datasets_checked", []):
        lines.append(f"### `{ds.get('name', 'unknown')}`")
        lines.append(f"- **Shape:** {ds.get('shape', 'N/A')}")
        if "date_range" in ds:
            lines.append(f"- **Date range:** {ds['date_range'].get('min', '?')} → {ds['date_range'].get('max', '?')}")
        if "grid_cells" in ds:
            lines.append(f"- **Grid cells:** {ds['grid_cells']:,}")
        if "spatial_extent" in ds:
            ext = ds["spatial_extent"]
            lines.append(f"- **Spatial extent:** lat [{ext.get('lat_min', '?'):.4f}, {ext.get('lat_max', '?'):.4f}], lon [{ext.get('lon_min', '?'):.4f}, {ext.get('lon_max', '?'):.4f}]")
        if "columns" in ds:
            lines.append(f"- **Columns:** {', '.join(ds['columns'])}")
        if "rainfall_stats" in ds:
            rs = ds["rainfall_stats"]
            lines.append(f"- **Rainfall stats:** min={rs.get('min_mm', '?'):.2f}, max={rs.get('max_mm', '?'):.2f}, mean={rs.get('mean_mm', '?'):.2f} mm")
        lines.append("")

    lines += ["\n---", "\n## QC Check Results", ""]
    checks = report.get("checks", {})
    status_icon = {"PASS": "✅", "WARN": "⚠️", "INFO": "ℹ️", "SKIP": "⏭️", "MISSING": "❌"}

    for check_name, result in checks.items():
        status = result.get("status", "?")
        icon = status_icon.get(status, "❓")
        lines.append(f"### {icon} {check_name.replace('_', ' ').title()}")
        lines.append(f"- **Status:** {status}")

        if check_name == "duplicates":
            lines.append(f"- Duplicate records: {result.get('duplicate_rows', '?')}")
        elif check_name == "missing_values":
            missing = result
            high_missing = {k: v for k, v in missing.items()
                            if isinstance(v, dict) and v.get("pct_missing", 0) > 0}
            if high_missing:
                lines.append("- **Columns with missing values:**")
                for col, info in high_missing.items():
                    lines.append(f"  - `{col}`: {info['pct_missing']:.1f}% missing ({info['n_missing']:,} rows)")
            else:
                lines.append("- No missing values in Sentinel-1 features ✓")
        elif check_name == "flood_label_distribution":
            if "class_distribution" in result:
                lines.append(f"- Class distribution: {result['class_distribution']}")
                lines.append(f"- Flood pixels: {result.get('flood_percentage', '?')}%")
                lines.append(f"- Class imbalance ratio: {result.get('class_imbalance_ratio', '?')}:1")
        elif check_name in ("rainfall_validation", "coordinate_validation", "sentinel1_validation"):
            issues = result.get("issues", [])
            if issues:
                lines.append("- Issues detected:")
                for issue in issues:
                    lines.append(f"  - ⚠️ {issue}")
            else:
                lines.append("- No issues detected ✓")
        elif check_name == "temporal_consistency":
            dates = result.get("unique_dates", [])
            lines.append(f"- Unique dates: {dates}")
        lines.append("")

    # Feature statistics table
    feat_stats = report.get("feature_statistics", {}).get("flood_features", {})
    if feat_stats:
        lines += ["\n---", "\n## Feature Statistics", "",
                  "| Column | Count | Mean | Std | Min | Median | Max | Outliers (3σ) |",
                  "|--------|-------|------|-----|-----|--------|-----|--------------|"]
        for col, stats in feat_stats.items():
            if isinstance(stats, dict) and "mean" in stats:
                lines.append(
                    f"| `{col}` | {stats.get('count', 0):,} | {stats.get('mean', 'NaN'):.4f} | "
                    f"{stats.get('std', 'NaN'):.4f} | {stats.get('min', 'NaN'):.4f} | "
                    f"{stats.get('median', 'NaN'):.4f} | {stats.get('max', 'NaN'):.4f} | "
                    f"{stats.get('n_outliers_3sigma', 0):,} |"
                )
            else:
                lines.append(f"| `{col}` | 0 | — | — | — | — | — | — |")

    lines += [
        "\n---",
        "\n## Known Limitations",
        "",
        "| Issue | Severity | Notes |",
        "|-------|----------|-------|",
        "| No ward/admin boundaries | HIGH | Cannot compute ward-level features — see WARD_BOUNDARIES_MISSING.md |",
        "| No DEM for AOI | HIGH | Raw DEM directory empty; test tile is wrong geographic area |",
        "| Single AOI date only | MEDIUM | Feature dataset covers one event (2021-10-06). Temporal features limited |",
        "| Single flood AOI | MEDIUM | Only one 10×10km patch. Not suitable for India-wide training |",
        "| fiona not installed | LOW | Hydrology data uses geopandas/pyogrio backend |",
        "| richdem not installable | LOW | Slope uses numpy gradient instead (requires C++ Build Tools) |",
        "",
        "---",
        "",
        "> **Report generated by Phase 3 Data Quality Control pipeline**",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log.info(f"QC Markdown report saved: {md_path}")


if __name__ == "__main__":
    run_quality_control()
