"""
Phase 3 — Master Runner
========================
Orchestrates all Phase 3 data processing pipeline steps in order.

Usage:
  python scripts/data_processing/run_phase3.py --sample   # Sample/test run
  python scripts/data_processing/run_phase3.py            # Full run
  python scripts/data_processing/run_phase3.py --step 2   # Single step

Steps:
  1: Dataset inspection (already done — run separately with inspect_datasets.py)
  2: Rainfall pipeline
  3: DEM pipeline
  4: Hydrology pipeline
  5: Admin/ward pipeline
  6: Feature assembly
  7: Quality control
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("phase3_runner")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts", "data_processing")
sys.path.insert(0, SCRIPTS_DIR)


def run_step(step_num, step_name, func, sample_only=False):
    """Run a single pipeline step with timing and error handling."""
    log.info("\n" + "=" * 70)
    log.info(f"STEP {step_num}: {step_name}")
    log.info("=" * 70)
    t0 = time.time()
    result = None
    status = "SUCCESS"
    try:
        result = func(sample_only) if "sample_only" in func.__code__.co_varnames else func()
    except Exception as e:
        log.error(f"STEP {step_num} FAILED: {e}")
        import traceback
        traceback.print_exc()
        status = "FAILED"
    elapsed = time.time() - t0
    log.info(f"STEP {step_num} {status} — elapsed: {elapsed:.1f}s")
    return result, status, elapsed


def main():
    parser = argparse.ArgumentParser(description="Phase 3 Master Pipeline Runner")
    parser.add_argument("--sample", action="store_true",
                        help="Run all pipelines on small samples for testing")
    parser.add_argument("--step", type=int, default=0,
                        help="Run only a specific step (2–7)")
    args = parser.parse_args()

    log.info("=" * 70)
    log.info("PHASE 3 — DATA PROCESSING PIPELINE")
    log.info(f"Mode: {'SAMPLE' if args.sample else 'FULL'}")
    log.info(f"Started: {datetime.now().isoformat()}")
    log.info("=" * 70)

    if args.sample:
        log.warning("SAMPLE MODE: Processing only small subsets for pipeline validation.")
        log.warning("For production features, re-run without --sample flag.")

    results = {}
    t_total = time.time()

    # ── Import pipeline modules ───────────────────────────────────────────────
    try:
        from rainfall_pipeline import run_rainfall_pipeline
        from dem_pipeline import run_dem_pipeline
        from hydrology_pipeline import run_hydrology_pipeline
        from admin_pipeline import run_admin_pipeline
        from feature_assembly import assemble_feature_dataset
        from quality_control import run_quality_control
    except ImportError as e:
        log.error(f"Failed to import pipeline module: {e}")
        sys.exit(1)

    # ── Pipeline steps ────────────────────────────────────────────────────────
    steps = {
        2: ("Rainfall Pipeline (IMD NetCDF)", run_rainfall_pipeline),
        3: ("DEM Pipeline", run_dem_pipeline),
        4: ("Hydrology Pipeline (Waterbodies + Rivers)", run_hydrology_pipeline),
        5: ("Admin/Ward Boundary Pipeline", run_admin_pipeline),
        6: ("Feature Dataset Assembly", assemble_feature_dataset),
        7: ("Quality Control", run_quality_control),
    }

    run_steps = [args.step] if args.step > 0 else list(steps.keys())

    for step_num in run_steps:
        if step_num not in steps:
            log.warning(f"Unknown step: {step_num}")
            continue
        step_name, func = steps[step_num]

        # Admin pipeline and QC don't take sample_only parameter
        if step_num in (5, 7):
            def make_wrapper(f):
                def wrapper(sample_only):
                    return f()
                return wrapper
            result, status, elapsed = run_step(step_num, step_name, make_wrapper(func), args.sample)
        else:
            result, status, elapsed = run_step(step_num, step_name, func, args.sample)

        results[step_num] = {"status": status, "elapsed_s": round(elapsed, 1)}

    # ── Summary ───────────────────────────────────────────────────────────────
    total_elapsed = time.time() - t_total
    log.info("\n" + "=" * 70)
    log.info("PHASE 3 PIPELINE SUMMARY")
    log.info("=" * 70)

    all_ok = True
    for step_num, res in results.items():
        step_name, _ = steps.get(step_num, (f"Step {step_num}", None))
        status = res["status"]
        elapsed = res["elapsed_s"]
        icon = "✓" if status == "SUCCESS" else "✗"
        log.info(f"  [{icon}] Step {step_num}: {step_name} — {status} ({elapsed}s)")
        if status != "SUCCESS":
            all_ok = False

    log.info(f"\nTotal elapsed: {total_elapsed:.1f}s")
    log.info(f"Final status: {'ALL STEPS SUCCEEDED' if all_ok else 'SOME STEPS FAILED'}")

    # List generated files
    features_dir = os.path.join(BASE_DIR, "data", "features")
    docs_dir = os.path.join(BASE_DIR, "docs")

    log.info("\n--- Generated files ---")
    for d, label in [(features_dir, "data/features"), (docs_dir, "docs")]:
        if os.path.isdir(d):
            for fname in sorted(os.listdir(d)):
                fpath = os.path.join(d, fname)
                size_kb = os.path.getsize(fpath) / 1024
                log.info(f"  {label}/{fname} ({size_kb:.1f} KB)")

    log.info("=" * 70)
    log.info("Phase 3 complete. DO NOT proceed to Phase 4 automatically.")
    log.info("Wait for user review and instruction before Phase 4.")
    log.info("=" * 70)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
